# -*- coding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2017 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Partner filter in account partner reports',
    'description': """
Partner filter
==============
Select partners from list to filter records in following reports:
1) Partner Ledger
2) Aged Receivable
3) Aged Payable
4) Customer Statements
    """,

    'version': '1.0',
    'category': 'Accounting',

    'author': 'Bista Solutions Inc.',
    'website': "http://www.bistasolutions.com",

    'depends': ['account', 'account_reports'],
    'data': [
        'views/search_template_view.xml',
        'views/res_config_view.xml'
    ],

    'installable': True,
    'auto_install': False
}
