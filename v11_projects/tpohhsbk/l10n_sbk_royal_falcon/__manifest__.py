# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Royal Falcon Security Services',
    'version': '1.0',
    'sequence': 7,
    'category': 'Localization',
    'summary': "COA of Royal Falcon Security Services",
    'description': """
Royal Falcon Security Services Accounting
======================================================================================
    * This module is provide configure COA for Royal Falcon Security Services company.
    """,
    'website': 'https://www.bistasolutions.com',
    'author': 'Bista Solutions',
    'images': [],
    'depends': ['sbk_group'],
    'data': [
        'data/res.company.csv',
        'data/account_chart_template_data.xml',
        'data/account.account.template.csv',
        'data/l10n_sbk_royal_falcon_chart_data.xml',
        'data/account_chart_template_data.yml',
        'data/account_tax_data.xml',
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
}
