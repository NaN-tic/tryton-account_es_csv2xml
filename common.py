# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import csv
from lxml import etree


def init_xml():
    xml = etree.Element('tryton')
    return xml


def get_csv_reader(file_name):
    try:
        reader = csv.reader(open(file_name, 'rU'), delimiter=str(','),
                            quotechar=str('"'))
    except:
        print ("Error reading %s csv file" % file_name)
        return []
    return reader


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
