# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "Import MX XML purchase invoice",
    'summary': """""",
    'description': """
    """,
    'author': "Yeidala",
    'license': 'OPL-1',
    'images': ['static/description/banners/banner.gif'],
    'website': "https://www.odoo.com/es_ES/partners/yeidala-1234306",
    'category': 'Location',
    'version': '14.0.0.0.2',
    'price': 149.99,
    'currency': 'USD',
    'depends': [
        'base',
        'account_accountant',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/data_sequence.xml',
        'views/account_move_views.xml',
        'views/xml_import_invoice_views.xml',
        'wizard/xml_import_wizard_views.xml',
    ],
    'external_dependencies': {
        'python': [
            'cfdiclient',
        ],
    },
}

