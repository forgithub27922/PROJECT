# -*- encoding: utf-8 -*-
##########################################################################################
#
#    Copyright (C) 2019 Skyscend Business Solutions (https://www.skyscendbs.com)
#    Copyright (C) 2020 Skyscend Business Solutions Pvt. Ltd. (https://www.skyscendbs.com)
#
##########################################################################################
{
    'name': 'Account Barcode',
    'version': '15.0.0.1',
    'category': 'account',
    'license': 'AGPL-3',
    'summary': 'Account Orders: Scan Barcodes on Accounting Order.',
    'description': """
    This module is used scan barcodes on the Accounting.
    """,
    'author': 'Skyscend Business Solutions Pvt. Ltd.',
    'website': 'https://www.skyscendbs.com',
    'depends': ['account', 'barcodes'],
    'data': [
        'views/account_move.xml',
    ],

    'installable': True,
    'auto_install': False,
    'application': True
}