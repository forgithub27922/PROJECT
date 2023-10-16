# -*- coding: utf-8 -*-

{
    'name': 'Dubai - Abu Dhabi Palace Accounting',
    'version': '1.1',
    'sequence': 4,
    'category': 'Localization',
    'summary': "COA of Abu Dhabi Palace",
    'description': """
Dubai - Abu Dhabi Palace Accounting
======================================
    * This module is provide configure COA for Abu Dhabi Palace company.
    """,
    'website': 'https://www.bistasolutions.com',
    'author': 'Bista Solutions',
    'images': [],
    'depends': ['sbk_group', 'account', 'l10n_multilang'],
    'data': [
        'data/account_chart_template_data.xml',
        'data/account.account.template.csv',
        'data/l10n_abu_dhabi_palace_chart_data.xml',
        'data/account_chart_template_data.yml',
        'data/account_tax_data.xml',
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
    # 'post_init_hook': 'load_translations',
}
