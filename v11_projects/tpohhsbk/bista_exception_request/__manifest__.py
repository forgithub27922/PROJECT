# -*- coding: utf-8 -*-

{'name': 'Exception Request',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'Employee can raise exception request',
    'description': """
Employee Roster and Payroll Management
======================================

exception request will be raised by employee and then approved by attendance manager/officer
    """,
    'author': 'Bista Solutions Pvt.Ltd.',
    'website': 'https://www.bistasolutions.com/',
    'depends': [
                'bista_hr_roster',
                ],
    'data': [
            'views/request_exception_view.xml',
            'views/roster_vs_attendance_inherit.xml',
            'security/security.xml',
            'security/ir.model.access.csv',
             ],
    'installable': True,
    'application': True,
    'auto_install': False,
 }
