# -*- coding: utf-8 -*-

{
    'name': 'Dubai - SBK Retail',
    'version': '1.0',
    'sequence': 9,
    'category': 'Localization',
    'summary': "COA of SBK Retail",
    'description': """
Dubai - SBK Retail
====================
    * This module is provide configure COA for SBK Retail company.
    """,
    'website': 'https://www.bistasolutions.com',
    'author': 'Bista Solutions',
    'images': [],
    'depends': ['sbk_group'],
    'data': [
        'data/account_chart_template_data.xml',
        'data/account.account.template.csv',
        'data/l10n_sbk_hospitality_chart_data.xml',
        'data/account_chart_template_data.yml',
        'data/account_tax_data.xml',
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
}
