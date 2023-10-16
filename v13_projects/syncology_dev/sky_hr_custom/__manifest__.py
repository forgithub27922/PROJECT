# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#
##############################################################################
{
    'name': 'Employees Custom',
    'version': '13.0.0.1',
    'category': 'HR',
    'description': """
    This module is used add custom menu""",
    'author': 'Skyscend Business Solutions',
    'website': 'http://www.skyscendbs.com',
    'depends': ['hr', 'hr_recruitment','hr_attendance', 'sky_emp_user', 'contacts'],
    'data': [
        'security/hr_security.xml',
        'security/ir.model.access.csv',
        'wizard/sky_change_job_position.xml',
        'views/sky_hr_custom_menu_view.xml',
        'views/hr_employee_view.xml',
        'views/hr_contract_view.xml',
        'views/hr_employee_status_view.xml',
        'views/hr_department_view.xml',
        'report/report_employee_template.xml',
        'report/employee_reports.xml',
        'data/schedule_time_crone.xml',
    ],
    'qweb': [
        'static/src/xml/base.xml',
    ],
    'installable': True,
    'auto_install': False
}
