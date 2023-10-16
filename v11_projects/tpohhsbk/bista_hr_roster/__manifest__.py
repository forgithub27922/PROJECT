# -*- coding: utf-8 -*-

{'name': 'Employee Roster',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'Employee Roster',
    'description': """
Employee Roster and Payroll Management
======================================

This application handle employee Roster, Shift, Roster VS Attandance.
Over Time request, Exception Request.
    """,
    'author': 'Bista Solutions Pvt.Ltd.',
    'website': 'https://www.bistasolutions.com/',
    'depends': ['hr_attendance',
                'hr_holidays',
                ],
    'data': ['data/ir_cron.xml',
              'data/weekoffday_data.xml',
              'wizard/change_shift_view.xml',
              'wizard/generate_roster_wizard.xml',
              'views/hr_roster_view.xml',
              'views/roster_vs_attendance.xml',
              'views/shift_view.xml',
              'views/hr_attendance_view.xml',
              'wizard/wiz_request_exception_view.xml',
              'security/ir.model.access.csv',
              'security/hr_roster_security.xml',
             'views/report_view.xml',
             'views/daily_performance_qweb_view.xml'
             ],
    'installable': True,
    'application': True,
    'auto_install': False,
 }
