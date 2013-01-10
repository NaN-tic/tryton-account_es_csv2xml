#!/usr/bin/python
# -*- coding: UTF-8 -*-
from lxml import etree
import csv

account_ids = []


def compute_code(account_id):
    return account_id.replace('pgc_', '')


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


def create_account_types(xml_data, file_name):
    # Read account_type csv file
    reader = get_csv_reader(file_name)
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
            ],
        }
        set_record(xml_data, record)


def create_accounts(xml_data, file_name):
    # Read account_csv file
    reader = get_csv_reader(file_name)
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
            ],
        }
        set_record(xml_data, record)
        account_ids.append(record['id'])


def create_tax_groups(xml_data, file_name):
    # Read tax_group csv file
    reader = get_csv_reader(file_name)
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


def create_tax_codes(xml_data, file_name):
    # Read tax_code csv file
    reader = get_csv_reader(file_name)
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
        set_record(xml_data, record)


def create_taxes(xml_data, file_names):
    for file_name in file_names:
        records = read_tax_file(file_name)
        for record in records:
            if record['fields'][len(record['fields']) - 1]['name'] == \
                    'account_name':
                record['fields'].pop()
            set_record(xml_data, record)


def create_tax_rules(xml_data, file_name):
    # Read tax_rule csv file
    reader = get_csv_reader(file_name)
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


def create_tax_rule_lines(tax_xml_data, file_name):
    reader = get_csv_reader(file_name)
    for row in reader:
        if reader.line_num == 1 or row[1] not in ['fp_intra', 'fp_extra']:
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
        set_record(tax_xml_data, record)


def read_tax_file(file_name):
    # Read tax csv file
    reader = get_csv_reader(file_name)
    records = []
    for row in reader:
        if reader.line_num == 1:
            continue
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
                {'name': 'percentage', 'eval': row[6]},
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
                {'name': 'account_name', 'text': row[18]},
            ],
        }
        records.append(tax_record)
    return records


def create_tax_accounts(account_xml_data):
    records = read_tax_file('tax_re.csv')
    records.extend(read_tax_file('tax_iva.csv'))
    records.extend(read_tax_file('tax_irpf.csv'))
    records.extend(read_tax_file('tax.csv'))
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
                if parent == 'pgc_4750':
                    kind = 'payable'
                elif parent == 'pgc_4700':
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
            set_record(account_xml_data, record)
            account_ids.append(record['id'])


def create_irpf_tax_rules(tax_xml_data, account_xml_data):

    def create_substitution_tax(tax_xml_data, group, record_id, name,
                                ref):
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
        set_record(tax_xml_data, record)
        return record

    def create_substitution_child_tax(tax_xml_data, tax_record, record_id,
                                      id_tail):
        record = tax_record.copy()
        record['id'] = record_id + id_tail
        record['fields'] = [f for f in record['fields'] if
                                f['name'] != 'account_name']
        record['fields'].extend([
            {'name': 'parent', 'ref': record_id},
        ])
        set_record(tax_xml_data, record)

    def create_tax_rule_lines(tax_xml_data, iva_record, irpf_record):
        reader = get_csv_reader('tax_rule.csv')
        percentage_irpf = irpf_record['id'].split('_')[-1:][0]
        for row in reader:
            if reader.line_num == 1 or not row[0].startswith('fp_irpf'):
                continue
            if percentage_irpf != row[0].replace('fp_irpf', ''):
                continue

            group = [f['ref'] for f in iva_record['fields'] if
                     f['name'] == 'group'][0]
            record = {
                'model': 'account.tax.rule.line.template',
                'id': row[0] + '+' + iva_record['id'],
                'fields': [
                    {'name': 'rule', 'ref': row[0]},
                    {'name': 'origin_tax', 'ref': iva_record['id']},
                    {'name': 'tax', 'ref': iva_record['id'] + '+' + \
                            irpf_record['id']},
                    {'name': 'group', 'ref': group},
                ],
            }
            set_record(tax_xml_data, record)
            break

#    create_tax_accounts(account_xml_data)
    iva_records = read_tax_file('tax_iva.csv')
    irpf_records = read_tax_file('tax_irpf.csv')

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
                create_substitution_tax(tax_xml_data, iva_group, record_id,
                                        complete_name, ref)
                create_substitution_child_tax(tax_xml_data, iva_record, record_id,
                                              '_iva_child')
                create_substitution_child_tax(tax_xml_data, irpf_record, record_id,
                                              '_irpf_child')
                create_tax_rule_lines(tax_xml_data, iva_record, irpf_record)


def create_re_tax_rules(tax_xml_data, account_xml_data):

    def create_substitution_tax(tax_xml_data, iva_id, re_id, iva_fields,
                                re_fields):
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
        set_record(tax_xml_data, record)
        return record

    def create_substitution_child_tax(tax_xml_data, fields, record_id,
                                      tail_id):
        record = {
            'model': 'account.tax.template',
            'id': record_id + tail_id,
            'fields': [{'name': 'parent', 'ref': record_id}],
        }
        fields = [f for f in fields if f['name'] != 'account_name']
        record['fields'].extend(fields)
        set_record(tax_xml_data, record)

    def create_tax_rule_line(tax_xml_data, row, tax_record):
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
        set_record(tax_xml_data, record)
#
#    create_tax_accounts(account_xml_data)

    iva_records = read_tax_file('tax_iva.csv')
    re_records = read_tax_file('tax_re.csv')
    re_reader = get_csv_reader('tax_rule_line.csv')

    old_source_tax = ''
    old_target_tax = ''
    for re_row in re_reader:
        if re_reader.line_num == 1 or re_row[1] != 'fp_recargo':
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
            tax_record = create_substitution_tax(tax_xml_data, iva_id, re_id,
                                                 iva_fields, re_fields)
            create_substitution_child_tax(tax_xml_data, iva_fields,
                                          tax_record['id'], '_iva_child')
            create_substitution_child_tax(tax_xml_data, re_fields,
                                          tax_record['id'], '_re_child')
            create_tax_rule_line(tax_xml_data, re_row, tax_record)


if __name__ == '__main__':
    # Initialize xml etree.Elements for each file
    account_xml, account_xml_data = init_xml()
    tax_xml, tax_xml_data = init_xml()

    # Next add data to each xml etree.Element
    # First to account_xml etree.Element
    create_account_types(account_xml_data, 'account_type.csv')
    create_accounts(account_xml_data, 'account.csv')
    create_tax_accounts(account_xml_data)
    # And then to tax_xml etree.Element
    create_tax_groups(tax_xml_data, 'tax_group.csv')
    create_tax_codes(tax_xml_data, 'tax_code.csv')
    create_taxes(tax_xml_data, [
        'tax.csv',
        'tax_iva.csv',
#        'tax_irpf.csv', # I believe that it is not necessary
#        'tax_re.csv', # I believe that it is not necessary
    ])
    create_tax_rules(tax_xml_data, 'tax_rule.csv')
    create_tax_rule_lines(tax_xml_data, 'tax_rule_line.csv')
    create_irpf_tax_rules(tax_xml_data, account_xml_data)
    create_re_tax_rules(tax_xml_data, account_xml_data)
    # Finally save each xml etree.Element to a file
    write_xml_file(account_xml, account_xml_data, 'account_es.xml')
    write_xml_file(tax_xml, tax_xml_data, 'tax_es.xml')
