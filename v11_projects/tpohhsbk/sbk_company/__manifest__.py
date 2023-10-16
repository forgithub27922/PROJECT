# -*- coding: utf-8 -*-

{
    'name': 'SBK Company',
    'version': '1.1',
    'sequence': 1,
    'category': 'Base',
    'summary': "Manage Companies",
    'description': """
SBK Company
==============
    * Create Companies.
    """,
    'website': 'https://www.bistasolutions.com',
    'author': 'Bista Solutions',
    'images': [],
    'depends': ['base',
    ],
    'data': [
        'data/company_data.xml',
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
    # 'post_init_hook': 'load_translations',
}
