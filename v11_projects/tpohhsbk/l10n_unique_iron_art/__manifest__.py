# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Unique Iron Art Manufacture of Cravings LLC',
    'version': '1.0',
    'sequence': 7,
    'category': 'Localization',
    'summary': "COA of Unique Iron Art Manufacture of Cravings LLC",
    'description': """
Unique Iron Art Manufacture of Cravings LLC Accounting
==========================================================================
    * This module is provide configure COA for Unique Iron Art Manufacture of Cravings LLC company.
    """,
    'website': 'https://www.bistasolutions.com',
    'author': 'Bista Solutions Pvt. Ltd.',
    'images': [],
    'depends': ['sbk_group'],
    'data': [
    	'data/res.company.csv',
        'data/account_chart_template_data.xml',
        'data/account.account.template.csv',
        'data/l10n_sbk_unique_iron_art_chart_data.xml',
        'data/account_chart_template_data.yml',
        'data/account_tax_data.xml',
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
}
