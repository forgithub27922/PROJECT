# -*- coding: utf-8 -*-

{
    'name': 'Dubai - SBK Holding',
    'version': '1.0',
    'sequence': 6,
    'category': 'Localization',
    'summary': "COA of SBK Holding",
    'description': """
Dubai - SBK Holding Accounting
===============================
    * This module is provide configure COA for SBK Holding company.
    """,
    'website': 'https://www.bistasolutions.com',
    'author': 'Bista Solutions',
    'images': [],
    'depends': ['sbk_group'],
    'data': [
        'data/account_chart_template_data.xml',
        'data/account.account.template.csv',
        'data/l10n_sbk_holding_chart_data.xml',
        'data/account_chart_template_data.yml',
        'data/account_tax_data.xml',
        # 'data/account.journal.csv'
        # 'data/res.partner.csv',
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
    # 'post_init_hook': 'load_translations',
}
