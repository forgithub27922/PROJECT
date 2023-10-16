# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2018 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Bista Import Trial Balance',
    'description': """
        This Module Allows You to Import Trail Balance company wise.
    """,
    'version': '1.0',
    'category': 'Account',
    'website': 'www.bistasolutions.com',
    'author': 'Bista Solutions Pvt. Ltd.',
    'maintainer': 'Bista Solutions Pvt. Ltd.',
    'depends': ['base', 'account_accountant'],
    'data': [
            'security/security.xml',
            'wizard/wizard_import_trial_balance.xml'
    ],
    'demo': [],
    'auto_install': False,
    'application': False,
    'installable': True
}
