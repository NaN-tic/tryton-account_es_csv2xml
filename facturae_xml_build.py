#!/usr/bin/python
# -*- coding: UTF-8 -*-
from common import (get_csv_reader, init_xml, normalize_xml, set_records,
    set_subelement, write_xml_file)

account_ids = []


def create_facturae_taxes(xml, iva_file, irpf_file, rule_lines_file,
        other_taxes_files):
    """ Creates taxes xml data for facturae module """
    # TODO: generate data for account_es_pyme with depends attribute
    xml_data = set_subelement(xml, 'data')

    # Read taxes csv files
    iva_rows = []
    for file in other_taxes_files + [iva_file]:
        records = []
        reader = get_csv_reader(file)
        module = 'account_es' if 'pyme' not in file else 'account_es_pyme'
        for row in reader:
            if reader.line_num == 1:
                continue
            if file == iva_file:
                iva_rows.append(row)
            assert len(row) >= 24, (
                "Expected row with at least 24 elements: %s" % len(row))
            if not row[27]:
                continue  # tax without report_type
            records.append({
                    'model': 'account.tax.template',
                    'id': module + '.' + row[0],
                    'fields': [
                        {'name': 'report_type', 'text': row[27]},
                        ],
                    })
        set_records(xml_data, records)

    irpf_records = []
    irpf_reader = get_csv_reader(irpf_file)
    for irpf_row in irpf_reader:
        if irpf_reader.line_num == 1:
            continue
        for iva_row in iva_rows:
            if iva_row[4] != irpf_row[4]:  # different groups
                continue
            assert len(irpf_row) >= 24, (
                "Expected row with at least 24 elements: %s" % len(irpf_row))
            assert len(iva_row) >= 24, (
                "Expected row with at least 24 elements: %s" % len(iva_row))
            record_id = iva_row[0] + '+' + irpf_row[0]
            if iva_row[27]:
                irpf_records.append({
                        'model': 'account.tax.template',
                        'id': module + '.' + record_id + '_iva_child',
                        'fields': [
                            {'name': 'report_type', 'text': iva_row[27]},
                            ],
                        })
            if irpf_row[27]:
                irpf_records.append({
                        'model': 'account.tax.template',
                        'id': module + '.' + record_id + '_irpf_child',
                        'fields': [
                            {'name': 'report_type', 'text': irpf_row[27]},
                            ],
                        })
    set_records(xml_data, irpf_records)

    re_records = []
    rule_lines_reader = get_csv_reader(rule_lines_file)
    for rl_row in rule_lines_reader:
        if rule_lines_reader.line_num == 1:
            continue
        if (rl_row[1] == 'fp_recc' or rl_row[1] == 'fp_pymes_recc'
                or (rl_row[1] != 'fp_recargo'
                    and rl_row[1] != 'fp_pymes_recargo')):
            continue

        new_source_tax = rl_row[2]
        new_target_tax = rl_row[3]
        if new_source_tax != new_target_tax:
            iva_id = new_source_tax
            re_id = new_target_tax
        else:
            continue

        for iva_row in iva_rows:
            if iva_row[0] != iva_id:
                continue
            if iva_row[4] != rl_row[4]:  # different groups
                continue
            assert len(iva_row) >= 24, (
                "Expected row with at least 24 elements: %s" % len(iva_row))
            if iva_row[27]:
                re_records.append({
                        'model': 'account.tax.template',
                        'id': '%s.%s+%s%s' % (
                            module, iva_id, re_id, '_iva_child'),
                        'fields': [
                            {'name': 'report_type', 'text': iva_row[27]},
                            ],
                        })
    set_records(xml_data, re_records)


if __name__ == '__main__':
    target_file = 'facturae/tax.xml'

    xml = init_xml()
    create_facturae_taxes(xml, 'tax_iva.csv', 'tax_irpf.csv',
        'tax_rule_line.csv', ['tax.csv', 'tax_igic.csv'])
    write_xml_file(xml, target_file)
    data = normalize_xml(target_file)
    with open(target_file, 'w') as f:
        f.write(data)
