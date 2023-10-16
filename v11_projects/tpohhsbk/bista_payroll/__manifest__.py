# -*- coding: utf-8 -*-

{
    'name': 'Bista Payroll',
    'version': '1.1',
    'sequence': 19,
    'category': 'Human Resources',
    'summary': "Manage Employee Payroll",
    'description': """
    """,
    'author': 'Bista Solutions Pvt. Ltd.',
    'website': 'https://www.bistasolutions.com',
    'depends': ['hr_payroll_account'],
    'data': [
        'security/payroll_security.xml',
        'views/templates.xml',
        'views/hr_payslip_view.xml',
        'wizard/send_mail_view.xml',
        'report/payslip_report.xml',
        'wizard/hr_payslip_payment_view.xml',
        'res/res_company_view.xml'
    ],
    'demo': [],
    'images': [],
    'application': True,
    'installable': True,
    'auto_install': False,
}
