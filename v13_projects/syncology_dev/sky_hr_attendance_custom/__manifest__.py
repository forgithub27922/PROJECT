# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#
##############################################################################
{
    'name': 'Attendance Custom',
    'version': '13.0.0.1',
    'category': 'HR',
    'description': """
    This module is used for attendance""",
    'author': 'Skyscend Business Solutions',
    'website': 'http://www.skyscendbs.com',
    'depends': ['hr_attendance', 'sky_hr_custom'],
    'data': [
        'views/hr_employee_view.xml',
        'wizard/import_attendance_wiz.xml',
        'security/ir.model.access.csv',
        'views/attendance_template.xml',
        'views/hr_attendance_view.xml',
    ],
    'qweb': [
        'static/src/xml/attendance_import.xml',
    ],
    'installable': True,
    'auto_install': False
}
