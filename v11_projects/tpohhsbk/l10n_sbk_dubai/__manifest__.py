# -*- coding: utf-8 -*-

{
    'name': 'Dubai - SBK Dubai Accounting',
    'version': '1.1',
    'sequence': 2,
    'category': 'Localization',
    'summary': "COA of SBK Dubai",
    'description': """
Dubai - SBK Dubai Accounting
===============================
    * This module is provide configure COA for SBK Dubai company.
    """,
    'website': 'https://www.bistasolutions.com',
    'author': 'Bista Solutions',
    'images': [],
    'depends': ['sbk_group'],
    'data': [
        'data/account_chart_template_data.xml',
        'data/account.account.template.csv',
        'data/l10n_sbk_dubai_chart_data.xml',
        'data/account_chart_template_data.yml',
        'data/account_tax_data.xml',
        # 'data/account.journal.csv'
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
    # 'post_init_hook': 'load_translations',
}
