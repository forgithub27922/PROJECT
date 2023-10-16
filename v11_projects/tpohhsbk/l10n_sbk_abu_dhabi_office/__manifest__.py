# -*- coding: utf-8 -*-

{
    'name': 'Dubai - SBK Abu Dhabi Office Accounting',
    'version': '1.1',
    'sequence': 3,
    'category': 'Localization',
    'summary': "COA of SBK Abu Dhabi Office",
    'description': """
Dubai - SBK Abu Dhabi Office Accounting
==========================================
    * This module is provide configure COA for SBK Abu Dhabi Office company.
    """,
    'website': 'https://www.bistasolutions.com',
    'author': 'Bista Solutions',
    'images': [],
    'depends': ['sbk_group'],
    'data': [
        'data/account_chart_template_data.xml',
        'data/account.account.template.csv',
        'data/l10n_l10n_sbk_abu_dhabi_office_chart_data.xml',
        'data/account_chart_template_data.yml',
        'data/account_tax_data.xml',
        # 'data/account.journal.csv',
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
    # 'post_init_hook': 'load_translations',
}
