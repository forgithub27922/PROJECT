# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#
##############################################################################
{
    'name': 'Sky Sms Hr',
    'version': '13.0.0.1',
    'category': 'HR',
    'description': """
    This module is used add custom field""",
    'author': 'Skyscend Business Solutions',
    'website': 'http://www.skyscendbs.com',
    'depends': ['sky_hr_custom', 'sms_core'],
    'data': ['security/ir.model.access.csv',
             'views/employee_grade_view.xml',
             'views/hr_employee_view.xml',
    ],
    'installable': True,
    'auto_install': False
}
