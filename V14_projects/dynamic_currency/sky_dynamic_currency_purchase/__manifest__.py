# -*- encoding: utf-8 -*-
##############################################################################
#
#    Skyscend Business Solutions
#    Copyright (C) 2019 (http://www.skyscendbs.com)
#
##############################################################################
{
    'name': 'Sky Dynamic Currency Purchase',
    'version': '14.0.0.1',
    'summary': 'Summery',
    'description': """
    """,
    'category': 'purchase',
    'author': 'Skyscend Business Solutions',
    'website': 'http://www.skyscendbs.com',
    'license': 'AGPL-3',
    'depends': ['base', 'purchase', 'sky_dynamic_currency_account'],
    'data': [
        'views/purchase.xml'
    ],
    'application': True,
    'installable': True,
    'auto_install': False
}
