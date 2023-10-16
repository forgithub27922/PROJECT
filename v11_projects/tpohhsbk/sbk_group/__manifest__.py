# -*- coding: utf-8 -*-

{
    'name': 'SBK Accounting Group',
    'version': '1.2',
    'sequence': 1,
    'category': 'Accounting',
    'summary': "Manage account groups of COA",
    'description': """
SBK Accounting Group
=======================
    * Create Account Groups.
    * Group sequence and COA order by group sequence.
    """,
    'website': 'https://www.bistasolutions.com',
    'author': 'Bista Solutions',
    'images': [],
    'depends': ['sbk_company', 'account_accountant'
    ],
    'data': [
        'data/account.group.csv',
        'views/account_group_view.xml',
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
}
