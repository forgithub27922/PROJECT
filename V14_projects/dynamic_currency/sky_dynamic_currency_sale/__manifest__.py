# -*- encoding: utf-8 -*-
##############################################################################
#
#    Skyscend Business Solutions
#    Copyright (C) 2019 (http://www.skyscendbs.com)
#
##############################################################################
{
    'name': 'Sky dynamic Currency Sale',
    'version': '14.0.0.1',
    'category': 'sale',
    'license': 'AGPL-3',
    'description': """
    """,
    'author': 'Skyscend Business Solutions',
    'website': 'http://www.skyscendbs.com',
    'depends': ['base','sky_dynamic_currency','sale_management','sky_dynamic_currency_account'],
    'data': [
            'views/sale_views.xml',
            ],
    'installable': True,
    'auto_install': False
}