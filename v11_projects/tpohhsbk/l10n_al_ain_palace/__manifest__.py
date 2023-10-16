# -*- coding: utf-8 -*-

{
    'name': 'Dubai - Al Ain Palace Accounting',
    'version': '1.1',
    'sequence': 5,
    'category': 'Localization',
    'summary': "COA of Al Ain Palace",
    'description': """
Dubai - Al Ain Palace Accounting
===================================
    * This module is provide configure COA for Al Ain Palace company.
    """,
    'website': 'https://www.bistasolutions.com',
    'author': 'Bista Solutions',
    'images': [],
    'depends': ['sbk_group', 'account', 'l10n_multilang'],
    'data': [
        'data/account_chart_template_data.xml',
        'data/account.account.template.csv',
        'data/l10n_al_ain_palace_chart_data.xml',
        'data/account_chart_template_data.yml',
        'data/account_tax_data.xml',
        # 'data/account.journal.csv',
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
    # 'post_init_hook': 'load_translations',
}
