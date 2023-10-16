# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Falcon Aviation',
    'version': '1.0',
    'sequence': 7,
    'category': 'Localization',
    'summary': "COA of Falcon Aviation",
    'description': """
Falcon Aviation Accounting
==========================================================================
    * This module is provide configure COA for Falcon Aviation company.
    """,
    'website': 'https://www.bistasolutions.com',
    'author': 'Bista Solutions',
    'images': [],
    'depends': ['sbk_group'],
    'data': [
        'data/res.company.csv',
        'data/account_chart_template_data.xml',
        'data/account.account.template.csv',
        'data/l10n_sbk_falcon_aviation_chart_data.xml',
        'data/account_chart_template_data.yml',
        'data/account_tax_data.xml',
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
}
