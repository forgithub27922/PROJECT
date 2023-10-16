# -*- encoding: utf-8 -*-
##############################################################################
#
#    Skyscend Business Solutions
#    Copyright (C) 2019 (http://www.skyscendbs.com)
#
##############################################################################
{
    'name': 'Sky dynamic Currency Account',
    'version': '14.0.0.1',
    'category': 'account',
    'license': 'AGPL-3',
    'description': """
    """,
    'author': 'Skyscend Business Solutions',
    'website': 'http://www.skyscendbs.com',
    'depends': ['base','sky_dynamic_currency','account'],
    'data': [
            'views/invoice.xml',
            'views/account_payment_register.xml'
            ],
    'installable': True,
    'auto_install': False
}
