#!/usr/bin/python
# -*- coding: UTF-8 -*-
from lxml import etree
import csv
import re

account_ids = []


def compute_code(account_id):
    if 'pymes' in account_id:
        code = account_id.replace('pgc_pymes_', '')
    else:
        code = account_id.replace('pgc_', '')
    code = code[:-2] + '%' + code[-2:]
    return code


def compute_parent(account_id):
    parent_id = account_id
    while parent_id not in account_ids:
        parent_id = parent_id[:-1]
        if not parent_id:
            print "Account parent of %s not found." % account_id
            break
    return parent_id


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


def write_xml_file(xml, xml_data, target_file):
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


def create_account_types(account_xml, file_name):
    # Read account_type csv file
    reader = get_csv_reader(file_name)
    levels = {
        0: [],
        }
    for row in reader:
        if reader.line_num == 1:
            continue
        record = {
            'model': 'account.account.type.template',
            'id': row[0],
            'fields': [
                {'name': 'name', 'text': row[1]},
                {'name': 'parent', 'ref': row[3]},
                {'name': 'sequence', 'eval': row[2]},
                {'name': 'balance_sheet', 'eval': row[4]},
                {'name': 'income_statement', 'eval': row[5]},
                {'name': 'display_balance', 'text': row[6]},
                ],
            }
        level = compute_level(record, levels)
        if level in levels:
            levels[level].append(record)
        else:
            levels[level] = [record]

    for level in levels:
        xml_data = set_subelement(account_xml, 'data', {'grouped': '1'})
        set_records(xml_data, levels[level])


def create_accounts(account_xml, file_name):
    # Read account_csv file
    reader = get_csv_reader(file_name)
    levels = {
        0: [],
        }
    for row in reader:
        if reader.line_num == 1:
            continue
        record = {
            'model': 'account.account.template',
            'id': row[0],
            'fields': [
                {'name': 'name', 'text': row[1]},
                {'name': 'parent', 'ref': row[3]},
                {'name': 'code', 'text': row[2]},
                {'name': 'reconcile', 'eval': row[4]},
                {'name': 'kind', 'text': row[5]},
                {'name': 'type', 'ref': row[6]},
                {'name': 'deferral', 'eval': row[7]},
                {'name': 'party_required', 'eval': row[8]},
            ],
        }
        level = compute_level(record, levels)
        if level in levels:
            levels[level].append(record)
        else:
            levels[level] = [record]
        account_ids.append(record['id'])

    for level in levels:
        xml_data = set_subelement(account_xml, 'data', {'grouped': '1'})
        set_records(xml_data, levels[level])


def create_tax_groups(tax_xml, file_name):
    # Read tax_group csv file
    reader = get_csv_reader(file_name)
    xml_data = set_subelement(tax_xml, 'data', {'grouped': '1'})
    for row in reader:
        if reader.line_num == 1:
            continue
        record = {
            'model': 'account.tax.group',
            'id': row[0],
            'fields': [
                {'name': 'name', 'text': row[1]},
                {'name': 'code', 'text': row[2]},
                {'name': 'kind', 'text': row[3]},
            ],
        }
        set_record(xml_data, record)


def create_tax_codes(tax_xml, file_name):
    # Read tax_code csv file
    reader = get_csv_reader(file_name)
    levels = {
        0: [],
        }
    for row in reader:
        if reader.line_num == 1:
            continue
        record = {
            'model': 'account.tax.code.template',
            'id': row[0],
            'fields': [
                {'name': 'name', 'text': row[1]},
                {'name': 'parent', 'ref': row[3]},
                {'name': 'code', 'text': row[2]},
                {'name': 'account', 'ref': row[4]},
            ],
        }
        level = compute_level(record, levels)
        if level in levels:
            levels[level].append(record)
        else:
            levels[level] = [record]
    for level in levels:
        xml_data = set_subelement(tax_xml, 'data', {'grouped': '1'})
        set_records(xml_data, levels[level])


def create_taxes(tax_xml, file_names):
    levels = {
        0: [],
        }
    for file_name in file_names:
        records = read_tax_file(file_name)
        for record in records:
            if record['fields'][len(record['fields']) - 1]['name'] == \
                    'account_name':
                record['fields'].pop()

            level = compute_level(record, levels)
            if level in levels:
                levels[level].append(record)
            else:
                levels[level] = [record]

    for level in levels:
        xml_data = set_subelement(tax_xml, 'data', {'grouped': '1'})
        set_records(xml_data, levels[level])


def create_tax_rules(tax_xml, file_name):
    # Read tax_rule csv file
    reader = get_csv_reader(file_name)
    xml_data = set_subelement(tax_xml, 'data', {'grouped': '1'})
    for row in reader:
        if reader.line_num == 1:
            continue
        record = {
            'model': 'account.tax.rule.template',
            'id': row[0],
            'fields': [
                {'name': 'name', 'text': row[1]},
                {'name': 'account', 'ref': row[2]},
                {'name': 'kind', 'text': row[3]},
            ],
        }
        set_record(xml_data, record)


def create_tax_rule_lines(tax_xml, file_name):
    reader = get_csv_reader(file_name)
    xml_data = set_subelement(tax_xml, 'data', {'grouped': '1'})
    for row in reader:
        if reader.line_num == 1 or row[1] not in ['fp_intra', 'fp_extra'] and \
                row[1] not in ['fp_pymes_intra', 'fp_pymes_extra']:
            continue
        record = {
            'model': 'account.tax.rule.line.template',
            'id': row[0],
            'fields': [
                {'name': 'rule', 'ref': row[1]},
                {'name': 'origin_tax', 'ref': row[2]},
                {'name': 'tax', 'ref': row[3]},
                {'name': 'group', 'ref': row[4]},
            ],
        }
        set_record(xml_data, record)


def read_tax_file(file_name):
    # Read tax csv file
    reader = get_csv_reader(file_name)
    records = []
    for row in reader:
        if reader.line_num == 1:
            continue
        rate = row[6]
        regex = re.compile("^Decimal\('(.*)'\)$")
        r = regex.search(rate)
        if r:
            value, = r.groups()
            rate = 'Decimal(\'%s\')' % str(float(value) / 100.0)
        tax_record = {
            'model': 'account.tax.template',
            'id': row[0],
            'fields': [
                {'name': 'name', 'text': row[1]},
                {'name': 'description', 'text': row[1]},
                {'name': 'parent', 'ref': row[2]},
                {'name': 'account', 'ref': row[3]},
                {'name': 'group', 'ref': row[4]},
                {'name': 'type', 'text': row[5]},
                {'name': 'rate', 'eval': rate},
                {'name': 'invoice_base_code', 'ref': row[7]},
                {'name': 'invoice_tax_code', 'ref': row[8]},
                {'name': 'credit_note_base_code', 'ref': row[9]},
                {'name': 'credit_note_tax_code', 'ref': row[10]},
                {'name': 'invoice_base_sign', 'eval': row[11]},
                {'name': 'invoice_tax_sign', 'eval': row[12]},
                {'name': 'credit_note_base_sign', 'eval': row[13]},
                {'name': 'credit_note_tax_sign', 'eval': row[14]},
                {'name': 'invoice_account', 'ref': row[15]},
                {'name': 'credit_note_account', 'ref': row[16]},
                {'name': 'sequence', 'text': row[17]},
                {'name': 'start_date', 'text': row[18]},
                {'name': 'end_date', 'text': row[19]},
                {'name': 'account_name', 'text': row[20]},
            ],
        }
        if len(row) >= 22:
            tax_record['fields'].append({
                    'name': 'report_description', 'text': row[21]})
        records.append(tax_record)
    return records


def create_tax_accounts(account_xml, file_names):
    records = []
    for file_name in file_names:
        records.extend(read_tax_file(file_name))
    # Maybe this mapping dictionary must go in the tax_....csv files in order
    # to reduce the code hard coded.
    map_2_type = {
        'pgc_4700': 'es_balance_normal_12360',
        'pgc_4700_child': 'es_balance_normal_12360',
        'pgc_472': 'es_balance_normal_12360',
        'pgc_473': 'es_balance_normal_12360',
        'pgc_4750': 'es_balance_normal_32560',
        'pgc_4750_child': 'es_balance_normal_32560',
        'pgc_4751': 'es_balance_normal_32560',
        'pgc_4770': 'es_balance_normal_32560',
        'pgc_4771': 'es_balance_normal_32560',

        'pgc_pymes_4700': 'es_balance_pymes_12390',
#        'pgc_pymes_4700_child': 'es_balance_pymes_12360',
        'pgc_pymes_472': 'es_balance_pymes_12390',
        'pgc_pymes_473': 'es_balance_pymes_12390',
        'pgc_pymes_4750': 'es_balance_pymes_32590',
#        'pgc_pymes_4750_child': 'es_balance_pymes_32560',
        'pgc_pymes_4751': 'es_balance_pymes_32590',
        'pg_pymesc_4770': 'es_balance_pymes_32590',
        'pgc_pymes_4771': 'es_balance_pymes_32590',
    }
    levels = {
        0: [],
        }
    for re_record in records:
        record = {
            'model': 'account.account.template',
            'fields': [],
        }
        for field in re_record['fields']:
            if field['name'] == 'invoice_account':
                record['id'] = field['ref']
                if record['id'] in account_ids:
                    break
                parent = compute_parent(field['ref'])
                record['fields'].extend([
                    {'name': 'code', 'text': compute_code(field['ref'])},
                    {'name': 'parent', 'ref': parent},
                ])
                if parent in map_2_type and parent:
                    account_type = map_2_type[parent]
                if parent == 'pgc_4750' or parent == 'pgc_pymes_4750':
                    kind = 'payable'
                elif parent == 'pgc_4700' or parent == 'pgc_pymes_4700':
                    kind = 'receivable'
                else:
                    kind = 'other'
            elif field['name'] == 'account_name':
                record['fields'].extend([
                    {'name': 'name', 'text': field['text']},
                ])
        record['fields'].extend([
            {'name': 'reconcile', 'eval': 'True'},
            {'name': 'kind', 'text': kind},
            {'name': 'type', 'ref': account_type},
            {'name': 'deferral', 'eval': 'True'},
        ])
        if record['id'] not in account_ids:
            level = compute_level(record, levels)
            if level in levels:
                levels[level].append(record)
            else:
                levels[level] = [record]
            account_ids.append(record['id'])

    for level in levels:
        xml_data = set_subelement(account_xml, 'data', {'grouped': '1'})
        set_records(xml_data, levels[level])


def create_irpf_tax_rules(tax_xml, account_xml_data, rule_file, iva_file,
                          irpf_file):

    def create_substitution_tax(group, record_id, name, ref):
        record = {
            'model': 'account.tax.template',
            'id': record_id,
            'fields': [
                {'name': 'name', 'text': name},
                {'name': 'account', 'ref': ref},
                {'name': 'description', 'text': name},
                {'name': 'type', 'text': 'none'},
                {'name': 'group', 'ref': group},
            ],
        }
        return record

    def create_substitution_child_tax(tax_record, record_id, id_tail):
        record = {}
        record['id'] = record_id + id_tail
        record['model'] = 'account.tax.template'
        record['fields'] = [f for f in tax_record['fields'] if
                                f['name'] not in ['account_name', 'parent']]
        record['fields'].append({'name': 'parent', 'ref': record_id})
        return record

    def create_tax_rule_lines(iva_record, irpf_record):
        reader = get_csv_reader(rule_file)
        rate_irpf = irpf_record['id'].split('_')[-1:][0]
        for row in reader:
            if reader.line_num == 1 or not row[0].startswith('fp_irpf') and \
                    not row[0].startswith('fp_pymes_irpf'):
                continue
            if rate_irpf != row[0].replace('fp_irpf', '') and \
                   rate_irpf != row[0].replace('fp_pymes_irpf', ''):
                continue
            group = [f['ref'] for f in iva_record['fields'] if
                     f['name'] == 'group'][0]
            record = {
                'model': 'account.tax.rule.line.template',
                'id': row[0] + '+' + iva_record['id'],
                'fields': [
                    {'name': 'rule', 'ref': row[0]},
                    {'name': 'origin_tax', 'ref': iva_record['id']},
                    {'name': 'tax', 'ref': iva_record['id'] + '+' +
                            irpf_record['id']},
                    {'name': 'group', 'ref': group},
                ],
            }
            return record

    levels = {
        0: [],
        }
    account_tax_rule_line_records = []
    iva_records = read_tax_file(iva_file)
    irpf_records = read_tax_file(irpf_file)

    for irpf_record in irpf_records:
        c = 0
        for field in irpf_record['fields']:
            if 'name' in field['name']:
                name = field['text']
                c += 1
            elif 'account' in field['name']:
                ref = field['ref']
                c += 1
            elif c >= 2:
                break
        for iva_record in iva_records:
            for field in iva_record['fields']:
                if 'name' in field['name']:
                    complete_name = name + ' + ' + field['text']
                    break
            record_id = iva_record['id'] + '+' + irpf_record['id']

            iva_group = [f['ref'] for f in iva_record['fields'] if
                     f['name'] == 'group'][0]
            irpf_group = [f['ref'] for f in irpf_record['fields'] if
                     f['name'] == 'group'][0]
            if iva_group == irpf_group:
                record = create_substitution_tax(iva_group, record_id,
                    complete_name, ref)
                level = compute_level(record, levels)
                if level in levels:
                    levels[level].append(record)
                else:
                    levels[level] = [record]

                record = create_substitution_child_tax(iva_record, record_id,
                    '_iva_child')
                level = compute_level(record, levels)
                if level in levels:
                    levels[level].append(record)
                else:
                    levels[level] = [record]

                record = create_substitution_child_tax(irpf_record, record_id,
                    '_irpf_child')
                level = compute_level(record, levels)
                if level in levels:
                    levels[level].append(record)
                else:
                    levels[level] = [record]

                account_tax_rule_line_records.append(create_tax_rule_lines(
                    iva_record, irpf_record))

    for level in levels:
        xml_data = set_subelement(tax_xml, 'data', {'grouped': '1'})
        set_records(xml_data, levels[level])
    xml_data = set_subelement(tax_xml, 'data', {'grouped': '1'})
    set_records(xml_data, account_tax_rule_line_records)


def create_re_tax_rules(tax_xml, account_xml_data, iva_file, re_file,
                        rule_line_file):

    def create_substitution_tax(iva_id, re_id, iva_fields, re_fields):
        record = {
            'model': 'account.tax.template',
            'id': iva_id + '+' + re_id,
            'fields': [],
        }
        for iva_field in iva_fields:
            if 'name' not in iva_field['name']:
                continue
            tax_name = iva_field['text']
            break
        assigned = 0
        for re_field in re_fields:
            if 'name' == re_field['name']:
                tax_name = tax_name + ' + ' + re_field['text']
                assigned += 1
            elif 'account' == re_field['name']:
                account = re_field['ref']
                assigned += 1
            elif 'group' == re_field['name']:
                group = re_field['ref']
                assigned += 1
            elif assigned >= 3:
                break
        record['fields'].extend([
            {'name': 'name', 'text': tax_name},
            {'name': 'description', 'text': tax_name},
            {'name': 'type', 'text': 'none'},
            {'name': 'account', 'ref': account},
            {'name': 'group', 'ref': group},
        ])
        return record

    def create_substitution_child_tax(fields, record_id, tail_id):
        record = {
            'model': 'account.tax.template',
            'id': record_id + tail_id,
            'fields': [{'name': 'parent', 'ref': record_id}],
        }
        fields = [f for f in fields if f['name'] != 'account_name']
        record['fields'].extend(fields)
        return record

    def create_tax_rule_line(row, tax_record):
        record = {
            'model': 'account.tax.rule.line.template',
            'id': row[0],
            'fields': [
                {'name': 'rule', 'ref': row[1]},
                {'name': 'origin_tax', 'ref': row[2]},
                {'name': 'tax', 'ref': tax_record['id']},
                {'name': 'group', 'ref': row[4]},
            ],
        }
        return record

    levels = {
        0: [],
        }
    account_tax_rule_line_records = []
    iva_records = read_tax_file(iva_file)
    re_records = read_tax_file(re_file)
    re_reader = get_csv_reader(rule_line_file)

    old_source_tax = ''
    old_target_tax = ''
    for re_row in re_reader:
        if re_reader.line_num == 1:
            continue
        if re_row[1] == 'fp_recc' or re_row[1] == 'fp_pymes_recc':
            #RECC lines are manually defined on file so no need of tax creation
            tax_record = {'id': re_row[3]}
            account_tax_rule_line_records.append(create_tax_rule_line(re_row,
                tax_record))
            continue
        if re_row[1] != 'fp_recargo' and re_row[1] != 'fp_pymes_recargo':
            continue
        new_source_tax = re_row[2]
        new_target_tax = re_row[3]
        if new_source_tax != old_source_tax:
            old_source_tax = new_source_tax
            old_target_tax = new_target_tax
            continue
        # Build name of tax.template with names of IVA plus RE
        for iva_record in iva_records:
            if new_source_tax == iva_record['id'] or \
                    old_source_tax == iva_record['id']:
                iva_id = iva_record['id']
                iva_fields = iva_record['fields']
                break
        for re_record in re_records:
            if new_target_tax == re_record['id'] or \
                    old_target_tax == re_record['id']:
                re_id = re_record['id']
                re_fields = re_record['fields']
                break

        iva_group = [f['ref'] for f in iva_record['fields'] if
                 f['name'] == 'group'][0]
        re_group = [f['ref'] for f in re_record['fields'] if
                 f['name'] == 'group'][0]
        if iva_group == re_group:

            tax_record = create_substitution_tax(iva_id, re_id, iva_fields,
                re_fields)
            level = compute_level(tax_record, levels)
            if level in levels:
                levels[level].append(tax_record)
            else:
                levels[level] = [tax_record]

            record = create_substitution_child_tax(iva_fields,
                tax_record['id'], '_iva_child')
            level = compute_level(record, levels)
            if level in levels:
                levels[level].append(record)
            else:
                levels[level] = [record]

            record = create_substitution_child_tax(re_fields,
                tax_record['id'], '_re_child')
            level = compute_level(record, levels)
            if level in levels:
                levels[level].append(record)
            else:
                levels[level] = [record]

            account_tax_rule_line_records.append(create_tax_rule_line(re_row,
                tax_record))

    for level in levels:
        xml_data = set_subelement(tax_xml, 'data', {'grouped': '1'})
        set_records(xml_data, levels[level])
    xml_data = set_subelement(tax_xml, 'data', {'grouped': '1'})
    set_records(xml_data, account_tax_rule_line_records)


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
    # Create xml standard files
    # Initialize xml etree.Elements for each file
    account_xml = init_xml()
    tax_xml = init_xml()

    # Next add data to each xml etree.Element
    # First to account_xml etree.Element
    create_account_types(account_xml, 'account_type.csv')
    create_accounts(account_xml, 'account.csv')
    create_tax_accounts(account_xml, ['tax_re.csv', 'tax_iva.csv',
            'tax_igic.csv', 'tax_irpf.csv', 'tax.csv'])
    # And then to tax_xml etree.Element
    create_tax_groups(tax_xml, 'tax_group.csv')
    create_tax_codes(tax_xml, 'tax_code.csv')
    create_taxes(tax_xml, [
        'tax.csv',
        'tax_iva.csv',
        'tax_igic.csv',
    ])
    create_tax_rules(tax_xml, 'tax_rule.csv')
    create_tax_rule_lines(tax_xml, 'tax_rule_line.csv')
    create_irpf_tax_rules(tax_xml, account_xml, 'tax_rule.csv',
            'tax_iva.csv', 'tax_irpf.csv')

    create_re_tax_rules(tax_xml, account_xml, 'tax_iva.csv',
            'tax_re.csv', 'tax_rule_line.csv')
    # Finally save each xml etree.Element to a file
    write_xml_file(account_xml, account_xml, 'ordinario/account.xml')
    write_xml_file(tax_xml, tax_xml, 'ordinario/tax.xml')

    # Create xml files for PYMES
    # Initialize xml etree.Elements for each file
    account_xml_pymes = init_xml()
    tax_xml_pymes = init_xml()

    # Next add data to each xml etree.Element
    # First to account_xml_pymes etree.Element
    create_account_types(account_xml_pymes, 'account_type_pymes.csv')
    create_accounts(account_xml_pymes, 'account_pymes.csv')
    create_tax_accounts(account_xml_pymes, ['tax_re_pymes.csv',
            'tax_iva_pymes.csv', 'tax_igic_pymes.csv', 'tax_irpf_pymes.csv',
            'tax_pymes.csv'])
    # And then to tax_xml_pymes etree.Element
    create_tax_groups(tax_xml_pymes, 'tax_group_pymes.csv')
    create_tax_codes(tax_xml_pymes, 'tax_code_pymes.csv')
    create_taxes(tax_xml_pymes, [
            'tax_pymes.csv',
            'tax_iva_pymes.csv',
            'tax_igic_pymes.csv',
    ])
    create_tax_rules(tax_xml_pymes, 'tax_rule_pymes.csv')
    create_tax_rule_lines(tax_xml_pymes, 'tax_rule_line_pymes.csv')
    create_irpf_tax_rules(tax_xml_pymes, account_xml_pymes,
            'tax_rule_pymes.csv', 'tax_iva_pymes.csv', 'tax_irpf_pymes.csv')
    create_re_tax_rules(tax_xml_pymes, account_xml_pymes,
            'tax_iva_pymes.csv', 'tax_re_pymes.csv', 'tax_rule_line_pymes.csv')
    # Finally save each xml etree.Element to a file
    write_xml_file(account_xml_pymes, account_xml_pymes,
           'pymes/account.xml')
    write_xml_file(tax_xml_pymes, tax_xml_pymes, 'pymes/tax.xml')
    archives = (
        'ordinario/account.xml',
        'ordinario/tax.xml',
        'pymes/account.xml',
        'pymes/tax.xml',
        )
    for archive in archives:
        data = normalize_xml(archive)
        with open(archive, 'w') as f:
            f.write(data)
