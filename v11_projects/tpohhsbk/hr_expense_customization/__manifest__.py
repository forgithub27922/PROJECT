# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Hr Expense Cutomization',
    'version': '1.0',
    'category': 'Expense',
    'description': """
    """,
    'author': 'Bista Solutions Pvt. Ltd.',
    'website': 'http://www.bistasolutions.com',
    'depends': [
        'hr_expense',
        'hr_admin'
    ],
    'data': [
        'views/hr_expense_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
