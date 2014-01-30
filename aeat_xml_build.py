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
    xml_data = etree.SubElement(xml, 'data')
    return xml, xml_data


def write_xml_file(xml, xml_data, target_file):
    xml_data = etree.ElementTree(xml)
    xml_data.write(target_file, encoding='UTF-8', method='xml',
        standalone=False, pretty_print=True)


def set_record(xml_data, record):

    def set_subelement(parent_xml_element, label, attrib, text=False):
        xml_element = etree.SubElement(parent_xml_element, label,
                                       attrib=attrib)
        if text:
            xml_element.text = text.decode('utf-8')
        return xml_element

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


def create_349(xml_data):
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

    # Read account_csv fileee
    reader = get_csv_reader('tax.csv')
    for row in reader:
        if reader.line_num == 1:
            continue
        if not 'Intracomunitario' in row[1]:
            continue
        keys = sale_keys if 'sale' in row[4] else purchase_keys
        default_direction = 'out' if 'sale' in row[4] else 'in'
        default_key = keys[0]
        for key in keys:
            records.append({
                'model': 'aeat.349.type-account.tax.template',
                'id': 'aeat_349_template_type_%s_%s' % (row[0], key),
                'fields': [
                    {'name': 'tax', 'ref': 'account_es.' + str(row[0])},
                    {'name': 'aeat_349_type',
                            'ref': 'aeat_349.aeat_349_key_%s' % key},
                ],
            })
        field_name = 'aeat349_default_%s_operation_key' % default_direction
        records.append({
            'model': 'account.tax.template',
            'id': 'account_es.' + row[0],
            'fields': [
                {'name': field_name,
                        'ref': 'aeat_349.aeat_349_key_%s' % default_key},
            ],
        })
    set_records(xml_data, records)


def create_340(xml_data):
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

    # Read account_csv fileee
    files = ['tax.csv', 'tax_iva.csv']
    for file in files:
        reader = get_csv_reader(file)
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
                        {'name': 'tax', 'ref': 'account_es.' + str(row[0])},
                        {'name': 'aeat_340_type', 'ref': aeat_key},
                    ],
                })
            field_name = 'aeat340_default_%s_book_key' % default_direction
            aeat_key = 'aeat_340_key_%s' % default_key
            records.append({
                'model': 'account.tax.template',
                'id': 'account_es.' + row[0],
                'fields': [
                    {'name': field_name, 'ref': aeat_key},
                ],
            })
    set_records(xml_data, records)

if __name__ == '__main__':
    xml, xml_data = init_xml()
    create_349(xml_data)
    write_xml_file(xml, xml_data, 'aeat/349.xml')

    xml, xml_data = init_xml()
    create_340(xml_data)
    write_xml_file(xml, xml_data, 'aeat/340.xml')
