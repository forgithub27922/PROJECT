# -*- coding: utf-8 -*-

{'name': 'Overtime Request',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'Employee can raise overtime request',
    'description': """
Employee Roster and Payroll Management
======================================

Overtime request will be raised by employee and then approved by manager 
    """,
    'author': 'Bista Solutions Pvt.Ltd.',
    'website': 'https://www.bistasolutions.com/',
    'depends': [
                'bista_hr_roster',
		        'hr_payroll',
                'bista_hr',
                ],
    'data': [
            'views/overtime_fields.xml',
            'views/request_overtime_view.xml',
            'views/hr_payslip_view_inherit.xml',
            'views/roster_vs_attendance_inherit.xml',
            'security/ir.model.access.csv',
            'security/security.xml',
             ],
    'installable': True,
    'application': True,
    'auto_install': False,
 }
