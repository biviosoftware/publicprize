# -*- coding: utf-8 -*-
""" PayPal processing

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""
import argh
import csv
import collections
import pprint

def sum_download(csv_file):
    'Aggregate the numbers of PayPal'
    d = collections.defaultdict(lambda: collections.defaultdict(int))
    with open(csv_file, 'rt',  encoding='ISO-8859-1') as f:
        cr = csv.DictReader(f)
        for r in cr:
            if r[' Type'] != 'Shopping Cart Item':
                continue
            g = int(float(r[' Gross']))
            c = d[r[' Item Title'].split()[0]]
            c[r[' Name']] += g
            c['total'] += g
    pprint.PrettyPrinter().pprint(d)

if __name__ == '__main__':
    argh.dispatch_commands([sum_download])
