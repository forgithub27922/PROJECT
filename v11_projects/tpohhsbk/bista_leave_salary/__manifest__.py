# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Leave Salary',
    'version': '1.0',
    'category': 'Human Resources',
    'description': """
            Leave Salary of employee
    """,
    'author': 'Bista Solutions Pvt. Ltd',
    'website': 'http://www.bistasolutions.com',
    'depends': ['hr_contract','hr_holiday_extended','bista_payroll'],
    'data': [
        'security/ir.model.access.csv',
        'security/salary_security.xml',
        'data/salary_rule.xml',
        'views/hr_salary_rule_view.xml',
        'views/view_hr_contract.xml',
        'views/hr_holidays_view.xml',
        'views/leave_salary_view.xml',
        'views/hr_payslip.xml',
        'wizard/leave_salary_line_wizard.xml',
        'views/leave_allocation_batch_view.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
