# -*- encoding: utf-8 -*-
##############################################################################
#
#    Skyscend Business Solutions
#    Copyright (C) 2019 (http://www.skyscendbs.com)
#
##############################################################################
{
    'name': 'Sky Dynamic Currency Payment',
    'version': '14.0.0.1',
    'summary': 'Summery',
    'description': """
    """,
    'category': 'account',
    'author': 'Skyscend Business Solutions',
    'website': 'http://www.skyscendbs.com',
    'license': 'AGPL-3',
    'depends': ['base', 'sky_dynamic_currency_account', 'account'],
    'data': [
        'views/account_payment_view.xml',
    ],
    'application': True,
    'installable': True,
    'auto_install': False
}
