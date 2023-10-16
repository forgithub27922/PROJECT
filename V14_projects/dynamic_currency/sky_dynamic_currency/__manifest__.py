# -*- encoding: utf-8 -*-
##############################################################################
#
#    Skyscend Business Solutions
#    Copyright (C) 2019 (http://www.skyscendbs.com)
#
##############################################################################
{
    'name': 'Sky dynamic Currency Amount',
    'version': '14.0.0.1',
    'category': 'account',
    'license': 'AGPL-3',
    'description': """
    """,
    'author': 'Skyscend Business Solutions',
    'website': 'http://www.skyscendbs.com',
    'depends': ['base',],
    'data': [
            'views/res_currency_rate_views.xml',
            'views/res_currency_views.xml'
            ],
    'installable': True,
    'auto_install': False
}
