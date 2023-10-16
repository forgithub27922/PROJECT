# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Bista HR Gratuity',
    'version': '1.1',
    'category': 'Human Resources',
    'summary': 'Calculating the Gratuity for employee.',
    'description': """
Bista HR Gratuity
====================
* Configuration gratuity (Payroll / Configuration / Gratuity).
* Display gratuity amount in every payslip.
* Menu: Employee Gratuity (Payroll / Employee Gratuity)
* In Employee added tab for gratuity display.
* Register employee Gratity contribution.
    """,
    'author': 'Bista Solutions Pvt. Ltd.',
    'website': 'http://www.bistasolutions.com',
    'depends': ['hr_payroll_account', 'bista_eos', 'bista_hr'],
    'data': [
        'security/gratuity_security.xml',
        'security/ir.model.access.csv',
        'data/gratuity_data.xml',
        'data/salary_rule_data.xml',
        'data/ir_cron.xml',
        'wizard/gratuity_advance_payment_wizard.xml',
        'views/res_company_view.xml',
        'views/res_partner_view.xml',
        'views/hr_view.xml',
        'views/hr_gratuity_view.xml',
    ],
    'installable': True,
}
