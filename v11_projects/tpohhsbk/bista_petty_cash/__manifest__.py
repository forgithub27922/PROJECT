# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Bista Petty Cash',
    'version': '2.2',
    'category': 'Manage Petty Cash',
    'description': """
Petty Cash Management
=========================
    * Manage petty cash for Employee & Partner.
    * Mange advance paid and remain payment.
    * Manage Reconcilation & Record payment history for Petty-cash.
    """,
    'author': 'Bista Solutions Pvt. Ltd.',
    'website': 'http://www.bistasolutions.com',
    'depends': ['account', 'bista_hr', 'bista_hr_gratuity'], # bista_hr_gratuity dependancy for partner_id field in HR
    'data': [

        'data/ir_sequence_data.xml',
        'wizard/return_petty_cash_view.xml',
        'views/voucher_petty_cash_view.xml',
        ],
    'installable': True,
}
