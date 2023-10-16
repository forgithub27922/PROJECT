# -*- coding: utf-8 -*-

{
    'name': 'Employee Loan Management',
    'version': '1.1',
    'sequence': 19,
    'category': 'Human Resources',
    'summary': "Manage Employee Loan",
    'description': """
       This module allow HR department to manage loan of employees.
       Loan notification employee Inbox
    """,
    'author': 'Bista Solutions Pvt. Ltd.',
    'website': 'https://www.bistasolutions.com',
    'depends': ['hr', 'account', 'hr_payroll','bista_payroll'],
    'data': [
        'security/user_groups.xml',
        'security/ir.model.access.csv',
        'views/loan_sequence.xml',
        'wizard/loan_report_print.xml',
        'wizard/loan_register_payment.xml',
        'views/employee_loan_view.xml',
        'views/loan_action_view.xml',
        'views/loan_menu_view.xml',
        'views/hr_payslip_view.xml',
        'data/hr_payroll_data.xml',
        'views/templates.xml',
        'wizard/loan_reject_form_view.xml',
        'wizard/reschedule_wiz_view.xml',
        'report/loan_request_report.xml',
        'report/report_register.xml',
        'report/loan_report.xml',
        'report/loan_summary_report.xml',
        'report/loan_installment_report.xml',
        'views/batch_employee_loan_view.xml'

    ],
    'demo': [],
    'images': [],
    'application': True,
    'installable': True,
    'auto_install': False,
}
