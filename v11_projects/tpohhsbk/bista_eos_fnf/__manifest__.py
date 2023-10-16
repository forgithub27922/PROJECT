# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Bista EOS F&F',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'Allow to calculate F&F for employee.',
    'description': """
Bista EOS F&F
====================
* Calculate F&F for employee.
    """,
    'author': "Bista Solutions",
    'website': 'http://www.bistasolutions.com',
    'depends': ['bista_eos', 'bista_employee_loan', 'hr_gratuity_extended',
                'hr_expense',  'hr_payroll',],
    'data': [
        'security/ir.model.access.csv',
        'wizard/wiz_confirmation_payslip.xml',
        'wizard/eos_fnf_payment_wizard.xml',
        'views/hr_eos_fnf_view.xml',
        'report/report.xml',
        'report/eos_fnf_report.xml'
    ],
    'installable': True,
}
