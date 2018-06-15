#!/usr/bin/python
# -*- coding: UTF-8 -*-
from common import (get_csv_reader, init_xml, normalize_xml, set_records,
    set_subelement, write_xml_file)

account_ids = []


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


def create_sii(xml, files):
    """ Creates xml data for 340 model """
    # Read account_csv files
    for file in files:
        records = []
        reader = get_csv_reader(file)
        module = 'account_es' if 'pyme' not in file else 'account_es_pyme'
        for row in reader:
            if reader.line_num == 1:
                continue

            value = {
                'model': 'account.tax.template',
                'id': module + "." + row[0],
                'fields': [
                    {'name': 'sii_book_key', 'text': str(row[29])},
                    {'name': 'sii_issued_key', 'text': row[30] and
                        str(row[30]).zfill(2) or ''},
                    {'name': 'sii_received_key', 'text': row[31] and
                        str(row[31]).zfill(2) or ''},
                    {'name': 'sii_intracomunity_key', 'text': row[32] and
                        str(row[32]).zfill(2) or ''},
                    {'name': 'sii_subjected_key', 'text': str(row[33])},
                    {'name': 'sii_excemption_key', 'text': str(row[34])},
                    {'name': 'tax_used', 'text': str(row[40])},
                    {'name': 'invoice_used', 'text': str(row[41])},
                    ],
                }
            records.append(value)

        xml_data = set_subelement(xml, 'data', {
                'grouped': '1',
                'depends': module,
                })
        set_records(xml_data, records)


def create_re_child_tax_sii(xml, rule_line_file):
    """ Creates xml data for SII model for child IVA taxes"""
    records = []
    rule_reader = get_csv_reader(rule_line_file)
    module = ('account_es' if 'pyme' not in rule_line_file
        else 'account_es_pyme')

    records = []
    for rule_row in rule_reader:
        if rule_reader.line_num == 1:
            continue
        if rule_row[1] not in ('fp_recargo', 'fp_pymes_recargo'):
            continue
        if rule_row[2] == rule_row[3]:
            # Get line with other tax id
            continue

        tax_record_id = rule_row[2] + '+' + rule_row[3]

        fields = [
            {'name': 'sii_book_key', 'text': rule_row[5] or ''},
            {'name': 'sii_issued_key', 'text': rule_row[6] and
                str(rule_row[6]).zfill(2) or ''},
            {'name': 'sii_received_key', 'text': rule_row[7] and
                str(rule_row[7]).zfill(2) or ''},
            {'name': 'sii_subjected_key', 'text': str(rule_row[9])},
            {'name': 'tax_used', 'text': str(rule_row[12])},
            {'name': 'invoice_used', 'text': str(rule_row[13])},
        ]

        records.append({
                'model': 'account.tax.template',
                'id': module + '.' + tax_record_id,
                'fields': fields,
                })
        records.append({
                'model': 'account.tax.template',
                'id': module + '.' + tax_record_id + "_iva_child",
                'fields': fields,
                })
        records.append({
                'model': 'account.tax.template',
                'id': module + '.' + tax_record_id + "_re_child",
                'fields': fields,
                })

    xml_data = set_subelement(xml, 'data', {
            'grouped': '1',
            'depends': module,
            })
    set_records(xml_data, records)


def create_irpf_child_tax_sii(xml, iva_file, irpf_file):
    """ Creates xml data for SII model for child IRPF IVA taxes"""
    records = []
    iva_reader = get_csv_reader(iva_file)
    module = ('account_es' if 'pyme' not in iva_file
        else 'account_es_pyme')

    records = []
    for row in iva_reader:
        if iva_reader.line_num == 1:
            continue
        irpf_reader = get_csv_reader(irpf_file)
        for irpf_row in irpf_reader:
            if irpf_reader.line_num == 1:
                continue
            if row[4] != irpf_row[4]:
                # differnt groups
                continue

            fields = [
                {'name': 'sii_book_key', 'text': str(row[29])},
                {'name': 'sii_issued_key', 'text': row[30] and
                    str(row[30]).zfill(2) or ''},
                {'name': 'sii_received_key', 'text': row[31] and
                    str(row[31]).zfill(2) or ''},
                {'name': 'sii_intracomunity_key', 'text': row[32] and
                    str(row[32]).zfill(2) or ''},
                {'name': 'sii_subjected_key', 'text': str(row[33])},
                {'name': 'sii_excemption_key', 'text': str(row[34])},
                {'name': 'tax_used', 'text': str(row[40])},
                {'name': 'invoice_used', 'text': str(row[41])},
                ]

            tax_record_id = row[0] + '+' + irpf_row[0]

            value = {
                'model': 'account.tax.template',
                'id': '%s.%s' % (module, tax_record_id),
                'fields': fields,
                }
            records.append(value)

            value = {
                'model': 'account.tax.template',
                'id': '%s.%s' % (module, tax_record_id+'_iva_child'),
                'fields': fields,
                }

            records.append(value)

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


def create_re_child_tax_340(xml, rule_line_file):
    """ Creates xml data for 340 model for child IVA taxes"""
    records = []
    rule_reader = get_csv_reader(rule_line_file)
    module = ('account_es' if 'pyme' not in rule_line_file
        else 'account_es_pyme')

    records = []
    for rule_row in rule_reader:
        if rule_reader.line_num == 1:
            continue
        if rule_row[1] not in ('fp_recargo', 'fp_pymes_recargo'):
            continue
        if rule_row[2] == rule_row[3]:
            # Get line with other tax id
            continue

        # Build name of tax.template with names of IVA plus RE
        iva_id = rule_row[2]
        other_id = rule_row[3]
        tax_record_id = iva_id + '+' + other_id + '_iva_child'

        keys = []
        default_direction = 'out' if 'sale' in rule_row[4] else 'in'
        if default_direction == 'in':
            keys.append('R')
        else:
            keys.append('E')
        # if 'inversión' in rule_row[1]:
        #     keys.append('I')
        if rule_row[1] == 'fp_intra':
            keys.append('U')
        default_key = keys[0]

        for key in keys:
            aeat_key = 'aeat_340_key_%s' % key
            records.append({
                    'model': 'aeat.340.type-account.tax.template',
                    'id': 'aeat_340_template_type_%s_%s' % (
                        tax_record_id, key),
                    'fields': [
                        {'name': 'tax', 'ref': module + '.' + tax_record_id},
                        {'name': 'aeat_340_type', 'ref': aeat_key},
                        ],
                    })
        field_name = 'aeat340_default_%s_book_key' % default_direction
        aeat_key = 'aeat_340_key_%s' % default_key
        records.append({
                'model': 'account.tax.template',
                'id': module + '.' + tax_record_id,
                'fields': [
                    {'name': field_name, 'ref': aeat_key},
                    ],
                })
    xml_data = set_subelement(xml, 'data', {
            'grouped': '1',
            'depends': module,
            })
    set_records(xml_data, records)


def create_irpf_child_tax_340(xml, iva_file, irpf_file):
    """ Creates xml data for 340 model for child IRPF IVA taxes"""
    records = []
    iva_reader = get_csv_reader(iva_file)
    module = ('account_es' if 'pyme' not in iva_file
        else 'account_es_pyme')

    records = []
    for iva_row in iva_reader:
        if iva_reader.line_num == 1:
            continue
        irpf_reader = get_csv_reader(irpf_file)
        for irpf_row in irpf_reader:
            if irpf_reader.line_num == 1:
                continue
            if iva_row[4] != irpf_row[4]:
                # differnt groups
                continue

            tax_record_id = iva_row[0] + '+' + irpf_row[0] + '_iva_child'

            keys = []
            default_direction = 'out' if 'sale' in iva_row[4] else 'in'
            if default_direction == 'in':
                if 'inv' in iva_row[0]:
                    keys.append('I')
                keys.append('R')
            else:
                keys.append('E')
            default_key = keys[0]

            for key in keys:
                aeat_key = 'aeat_340_key_%s' % key
                records.append({
                        'model': 'aeat.340.type-account.tax.template',
                        'id': 'aeat_340_template_type_%s_%s' % (
                            tax_record_id, key),
                        'fields': [
                            {'name': 'tax', 'ref': module + '.'
                                + tax_record_id},
                            {'name': 'aeat_340_type', 'ref': aeat_key},
                            ],
                        })
            field_name = 'aeat340_default_%s_book_key' % default_direction
            aeat_key = 'aeat_340_key_%s' % default_key
            records.append({
                    'model': 'account.tax.template',
                    'id': module + '.' + tax_record_id,
                    'fields': [
                        {'name': field_name, 'ref': aeat_key},
                        ],
                    })
    xml_data = set_subelement(xml, 'data', {
            'grouped': '1',
            'depends': module,
            })
    set_records(xml_data, records)


def create_347(xml, files):
    """ Creates xml data for 347 model """
    # Read account_csv files
    for file in files:
        records = []
        reader = get_csv_reader(file)
        module = 'account_es' if 'pyme' not in file else 'account_es_pyme'
        for row in reader:
            if reader.line_num == 1:
                continue

            if not row[39]:
                include_347 = True
            else:
                include_347 = row[39]

            value = {
                'model': 'account.tax.template',
                'id': module + "." + row[0],
                'fields': [
                    {'name': 'include_347', 'eval': include_347},
                    ],
                }
            records.append(value)

        xml_data = set_subelement(xml, 'data', {
                'grouped': '1',
                'depends': module,
                })
        set_records(xml_data, records)


def create_irpf_child_tax_347(xml, iva_file, irpf_file):
    """ Creates xml data for 347 model for child IRPF IVA taxes"""
    records = []
    iva_reader = get_csv_reader(iva_file)
    module = 'account_es' if 'pyme' not in iva_file else 'account_es_pyme'

    records = []
    for row in iva_reader:
        if iva_reader.line_num == 1:
            continue
        irpf_reader = get_csv_reader(irpf_file)
        for irpf_row in irpf_reader:
            if irpf_reader.line_num == 1:
                continue
            if row[4] != irpf_row[4]:
                # differnt groups
                continue

            if not row[39]:
                include_347 = True
            else:
                include_347 = row[39]

            if not irpf_row[39]:
                irpf_include_347 = True
            else:
                irpf_include_347 = irpf_row[39]

            fields = [
                {'name': 'include_347', 'eval': include_347},
                ]

            irpf_fields = [
                {'name': 'include_347', 'eval': irpf_include_347},
                ]

            tax_record_id = row[0] + '+' + irpf_row[0]

            value = {
                'model': 'account.tax.template',
                'id': '%s.%s' % (module, tax_record_id),
                'fields': irpf_fields,
                }
            records.append(value)

            value = {
                'model': 'account.tax.template',
                'id': '%s.%s' % (module, tax_record_id + '_iva_child'),
                'fields': fields,
                }
            records.append(value)

            value = {
                'model': 'account.tax.template',
                'id': '%s.%s' % (module, tax_record_id + '_irpf_child'),
                'fields': irpf_fields,
                }
            records.append(value)

    xml_data = set_subelement(xml, 'data', {
            'grouped': '1',
            'depends': module,
            })
    set_records(xml_data, records)


if __name__ == '__main__':
    xml = init_xml()
    files = ['tax.csv', 'tax_pymes.csv', 'tax_igic.csv']
    create_349(xml, files)
    write_xml_file(xml, 'aeat/349.xml')

    xml = init_xml()
    files = ['tax.csv', 'tax_iva.csv', 'tax_pymes.csv', 'tax_iva_pymes.csv']
    create_340(xml, files)
    create_re_child_tax_340(xml, 'tax_rule_line.csv')
    create_re_child_tax_340(xml, 'tax_rule_line_pymes.csv')
    create_irpf_child_tax_340(xml, 'tax_iva.csv', 'tax_irpf.csv')
    create_irpf_child_tax_340(xml, 'tax_iva_pymes.csv', 'tax_irpf_pymes.csv')
    write_xml_file(xml, 'aeat/340.xml')

    xml = init_xml()
    files = ['tax.csv', 'tax_iva.csv', 'tax_pymes.csv', 'tax_iva_pymes.csv']
    create_347(xml, files)
    create_irpf_child_tax_347(xml, 'tax_iva.csv', 'tax_irpf.csv')
    create_irpf_child_tax_347(xml, 'tax_iva_pymes.csv', 'tax_irpf_pymes.csv')
    write_xml_file(xml, 'aeat/347.xml')

    xml = init_xml()
    files = ['tax.csv', 'tax_iva.csv', 'tax_irpf.csv', 'tax_pymes.csv',
        'tax_iva_pymes.csv', 'tax_irpf_pymes.csv']
    create_sii(xml, files)
    create_re_child_tax_sii(xml, 'tax_rule_line.csv')
    create_re_child_tax_sii(xml, 'tax_rule_line_pymes.csv')
    create_irpf_child_tax_sii(xml, 'tax_iva.csv', 'tax_irpf.csv')
    create_irpf_child_tax_sii(xml, 'tax_iva_pymes.csv', 'tax_irpf_pymes.csv')
    write_xml_file(xml, 'aeat/sii.xml')

    archives = (
        'aeat/349.xml',
        'aeat/340.xml',
        'aeat/347.xml',
        'aeat/sii.xml',
        )
    for archive in archives:
        data = normalize_xml(archive)
        with open(archive, 'w') as f:
            f.write(data)
