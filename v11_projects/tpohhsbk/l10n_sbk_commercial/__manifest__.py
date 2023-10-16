# -*- coding: utf-8 -*-

{
    'name': 'Dubai - SBK Commercial',
    'version': '1.0',
    'sequence': 7,
    'category': 'Localization',
    'summary': "COA of SBK Commercial",
    'description': """
Dubai - SBK Commercial Accounting
====================================
    * This module is provide configure COA for SBK Commercial company.
    """,
    'website': 'https://www.bistasolutions.com',
    'author': 'Bista Solutions',
    'images': [],
    'depends': ['sbk_group'],
    'data': [
        'data/account_chart_template_data.xml',
        'data/account.account.template.csv',
        'data/l10n_sbk_commercial_chart_data.xml',
        'data/account_chart_template_data.yml',
        'data/account_tax_data.xml',
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
}
