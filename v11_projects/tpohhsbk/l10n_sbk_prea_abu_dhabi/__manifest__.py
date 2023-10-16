# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Dubai - SBK PREA Abu Dhabi',
    'version': '1.0',
    'sequence': 7,
    'category': 'Localization',
    'summary': "COA of SBK PREA Abu Dhabi",
    'description': """
Dubai - SBK PREA Abu Dhabi Accounting
==========================================================================
    * This module is provide configure COA for SBK PREA Abu Dhabi company.
    """,
    'website': 'https://www.bistasolutions.com',
    'author': 'Bista Solutions',
    'images': [],
    'depends': ['sbk_group'],
    'data': [
        'data/res.company.csv',
        'data/account_chart_template_data.xml',
        'data/account.account.template.csv',
        'data/l10n_sbk_prea_abu_dhabi_chart_data.xml',
        'data/account_chart_template_data.yml',
        'data/account_tax_data.xml',
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
}
