#!/usr/bin/python
# -*- coding: UTF-8 -*-
from lxml import etree
import csv

account_ids = []


def compute_code(account_id):
    if 'pymes' in account_id:
        code = account_id.replace('pgc_pymes_', '')
    else:
        code = account_id.replace('pgc_', '')
    code = code[:-2] + '%' + code[-2:]
    return code


def get_csv_reader(file_name):
    try:
        reader = csv.reader(open(file_name, 'rU'), delimiter=str(','),
                            quotechar=str('"'))
    except:
        print ("Error reading %s csv file" % file_name)
        return []
    return reader


def init_xml():
    xml = etree.Element('tryton')
    return xml


def write_xml_file(xml, target_file):
    xml_data = etree.ElementTree(xml)
    xml_data.write(target_file, encoding='UTF-8', method='xml',
        standalone=False, pretty_print=True)


def set_subelement(parent_xml_element, label, attrib=None, text=None):
    if attrib:
        xml_element = etree.SubElement(parent_xml_element, label,
            attrib=attrib)
    else:
        xml_element = etree.SubElement(parent_xml_element, label)
    if text:
        xml_element.text = text.decode('utf-8')
    return xml_element


def set_record(xml_data, record):

    attrib = {
        'model': record['model'],
        'id': record['id'],
    }
    xml_record = set_subelement(xml_data, 'record', attrib)
    for field in record['fields']:
        text = False
        attrib = {'name': field['name']}
        if 'eval' in field and field.get('eval'):
            attrib.update({'eval': field['eval']})
        elif 'ref' in field and field.get('ref'):
            attrib.update({'ref': field['ref']})
        elif 'text' in field and field.get('text'):
            text = field['text']
        else:
            continue
        set_subelement(xml_record, 'field', attrib, text)


def set_records(xml_data, records):
    for record in records:
        set_record(xml_data, record)


def compute_level(record, levels):
    parent = None
    for field in record['fields']:
        if field['name'] == 'parent':
            parent = field['ref']
            break
    if parent:
        for level in levels:
            for record in levels[level]:
                if parent == record['id']:
                    return level + 1
    return 0


def create_349(xml, files):
    """ Creates xml data for 349 model """
    records = []
    sale_keys = ['E', 'H', 'M', 'T']
    purchase_keys = ['A', 'I', 'S', 'T']
    for key in list(set(sale_keys + purchase_keys)):
        records.append({
            'model': 'aeat.349.type',
            'id': 'aeat_349_key_%s' % key,
            'fields': [
                {'name': 'operation_key', 'text': key},
            ],
        })
    xml_data = set_subelement(xml, 'data', {
            'grouped': '1'
            })
    set_records(xml_data, records)

    # Read account_csv files
    for file in files:
        records = []
        reader = get_csv_reader(file)
        module = 'account_es' if 'pyme' not in file else 'account_es_pyme'
        for row in reader:
            if reader.line_num == 1:
                continue
            if 'Intracomunitario' not in row[1]:
                continue
            keys = sale_keys if 'sale' in row[4] else purchase_keys
            default_direction = 'out' if 'sale' in row[4] else 'in'
            default_key = keys[0]
            for key in keys:
                records.append({
                    'model': 'aeat.349.type-account.tax.template',
                    'id': 'aeat_349_template_type_%s_%s' % (row[0], key),
                    'fields': [
                        {'name': 'tax', 'ref': module + '.' + str(row[0])},
                        {'name': 'aeat_349_type',
                                'ref': 'aeat_349_key_%s' % key},
                    ],
                })
            field_name = 'aeat349_default_%s_operation_key' % default_direction
            records.append({
                'model': 'account.tax.template',
                'id': module + '.' + row[0],
                'fields': [
                    {'name': field_name,
                            'ref': 'aeat_349_key_%s' % default_key},
                ],
            })
        xml_data = set_subelement(xml, 'data', {
                'grouped': '1',
                'depends': module,
                })
        set_records(xml_data, records)


def create_340(xml, files):
    """ Creates xml data for 340 model """
    records = []
    keys = ['E', 'I', 'R', 'U']
    for key in keys:
        records.append({
            'model': 'aeat.340.type',
            'id': 'aeat_340_key_%s' % key,
            'fields': [
                {'name': 'book_key', 'text': key},
            ],
        })
    xml_data = set_subelement(xml, 'data', {
            'grouped': '1'
            })
    set_records(xml_data, records)

    # Read account_csv files
    for file in files:
        records = []
        reader = get_csv_reader(file)
        module = 'account_es' if 'pyme' not in file else 'account_es_pyme'
        for row in reader:
            if reader.line_num == 1:
                continue
            keys = []
            default_direction = 'out' if 'sale' in row[4] else 'in'
            if default_direction == 'in':
                keys.append('R')
            else:
                keys.append('E')
            if 'inversión' in row[1]:
                keys.append('I')
            if 'Intracomunitario' in row[1]:
                keys.append('U')

            default_key = keys[0]
            for key in keys:
                aeat_key = 'aeat_340_key_%s' % key
                records.append({
                    'model': 'aeat.340.type-account.tax.template',
                    'id': 'aeat_340_template_type_%s_%s' % (row[0], key),
                    'fields': [
                        {'name': 'tax', 'ref': module + '.' + str(row[0])},
                        {'name': 'aeat_340_type', 'ref': aeat_key},
                    ],
                })
            field_name = 'aeat340_default_%s_book_key' % default_direction
            aeat_key = 'aeat_340_key_%s' % default_key
            records.append({
                'model': 'account.tax.template',
                'id': module + '.' + row[0],
                'fields': [
                    {'name': field_name, 'ref': aeat_key},
                ],
            })
        xml_data = set_subelement(xml, 'data', {
                'grouped': '1',
                'depends': module,
                })
        set_records(xml_data, records)


def normalize_xml(archive):
    data = ''
    for line in open(archive):
        spaces = 0
        char = line[0]
        while char == ' ':
            spaces += 1
            char = line[spaces]
        spaces *= 2
        line = line.strip()
        if "encoding='UTF-8'" in line:
            line = (line.replace("encoding='UTF-8'", '').
                    replace("standalone='no'", '').replace('  ?', '?'))
            line += ('\n<!-- This file is part of Tryton.  The COPYRIGHT file '
                'at the top level of\nthis repository contains the full '
                'copyright notices and license terms. -->')
            data += ' ' * spaces + line + '\n'
        elif 'tryton' in line or 'data' in line:
            data += ' ' * spaces + line + '\n'
        else:
            line = line.strip('<>')
            if '">' not in line and '</' not in line:
                ends_label = False
                if line[-1] == '/':
                    ends_label = True
                    line = line.strip('/')
                model_attr = 0
                id_attr = 0
                name_attr = 0
                ref_attr = 0
                eval_attr = 0
                words = line.split()
                for word in words:
                    if 'model' in word:
                        model_attr = words.index(word)
                    elif 'id' in word:
                        id_attr = words.index(word)
                    elif 'name' in word:
                        name_attr = words.index(word)
                    elif 'ref' in word:
                        ref_attr = words.index(word)
                    elif 'eval' in word:
                        eval_attr = words.index(word)
                if id_attr and model_attr > id_attr:
                    words[id_attr], words[model_attr] = (
                        words[model_attr], words[id_attr])
                elif ref_attr and name_attr > ref_attr:
                    words[ref_attr], words[name_attr] = (
                        words[name_attr], words[ref_attr])
                elif eval_attr and name_attr > eval_attr:
                    words[eval_attr], words[name_attr] = (
                        words[name_attr], words[eval_attr])
                if ends_label:
                    line = '<' + ' '.join([w for w in words]) + '/>'
                else:
                    line = '<' + ' '.join([w for w in words]) + '>'
            else:
                line = '<' + line + '>'
            data += ' ' * spaces + line + '\n'
    return data

if __name__ == '__main__':
    xml = init_xml()
    files = ['tax.csv', 'tax_pymes.csv']
    create_349(xml, files)
    write_xml_file(xml, 'aeat/349.xml')

    xml = init_xml()
    files = ['tax.csv', 'tax_iva.csv', 'tax_pymes.csv', 'tax_iva_pymes.csv']
    create_340(xml, files)
    write_xml_file(xml, 'aeat/340.xml')

    archives = (
        'aeat/349.xml',
        'aeat/340.xml',
        )
    for archive in archives:
        data = normalize_xml(archive)
        with open(archive, 'w') as f:
            f.write(data)
