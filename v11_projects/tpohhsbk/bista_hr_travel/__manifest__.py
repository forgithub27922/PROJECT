# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Bista HR Travel',
    'version': '2.0',
    'category': 'Generic Modules',
    'description': """
            Travel Details of employee
    """,
    'author': 'Bista Solutions Pvt. Ltd',
    'website': 'http://www.bistasolutions.com',
    'depends': ['bista_hr', 'bista_hr_expense_reimburse', 'hr_payroll'],
    'data': [
        "security/ir.model.access.csv",
        "security/travel_security.xml",
        "views/hr_travel.xml",
        "wizard/wiz_allowance_view.xml"
    ],
    'installable': True,
}
