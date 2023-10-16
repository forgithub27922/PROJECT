# -*- coding: utf-8 -*-

{
    'name': 'Grimm Sale Purchase Report',
    'version': '0.3.0',
    'author': 'Viet Pham, Grimm Gastronomiebedarf GmbH',
    'summary': 'Grimm Report between Sale & Purchase',
    'website': 'https://www.grimm-gastrobedarf.de/',
    'category': 'Report',
    'depends': ['product', 'sale', 'purchase', 'account'],
    'data': [
        'views/sale_purchase_report_view.xml',
        'views/out_in_invoice_report_view.xml',
        'security/ir.model.access.csv',
    ],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
