# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'SBK Mina Al Fajer',
    'version': '1.0',
    'sequence': 7,
    'category': 'Localization',
    'summary': "COA of SBK Mina Al Fajer",
    'description': """
Dubai - SBK Mina Al Fajer Accounting
==========================================================================
    * This module is provide configure COA for SBK Mina Al Fajer company.
    """,
    'website': 'https://www.bistasolutions.com',
    'author': 'Bista Solutions',
    'images': [],
    'depends': ['sbk_group'],
    'data': [
        'data/res.company.csv',
        'data/account_chart_template_data.xml',
        'data/account.account.template.csv',
        'data/l10n_sbk_mina_al_fajer_chart_data.xml',
        'data/account_chart_template_data.yml',
        'data/account_tax_data.xml',
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
}
