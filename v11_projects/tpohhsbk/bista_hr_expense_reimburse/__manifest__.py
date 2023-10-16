# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Bista HR Expense',
    'version': '11.0.0.1',
    'category': 'HR',
    'description': """

    """,
    'author': 'Bista Solutions Pvt. Ltd',
    'website': 'http://www.bistasolutions.com',
    'depends': ['hr_expense','base'],
    'data': [
        "security/bista_hr_expense_reimburse_security.xml",
        "views/hr_expense_view.xml",
        "views/hr_expense_sheet_view.xml",
    ],
    'installable': True,
    'auto-install': False
}
