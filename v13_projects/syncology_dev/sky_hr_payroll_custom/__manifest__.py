# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#    Copyright (C) 2020 Skyscend Business Solutions Pvt. Ltd.(http://www.skyscendbs.com)
#
##############################################################################
{
    'name': 'Payroll',
    'version': '13.0.0.1',
    'category': 'HR',
    'description': """
    This module is used for additions""",
    'author': 'Skyscend Business Solutions Pvt. Ltd.',
    'website': 'http://www.skyscendbs.com',
    'depends': ['sky_hr_custom',
                'sky_hr_attendance_custom',
                'sky_hr_time_tracking_holidays_custom'
    ],
    'data': [
        'security/hr_payroll_security.xml',
        'security/ir.model.access.csv',
        'views/hr_addition_view.xml',
        'views/hr_penalty_view.xml',
        'views/hr_addition_reject_wizard_view.xml',
        'views/hr_employee_salary_view.xml',
        'views/hr_employee_view.xml',
        'views/res_config_settings_view.xml',
        'views/hr_time_tracking_view.xml',
        'views/hr_salary_report_wizard_view.xml',
        'data/salary_cron.xml',
        'data/ir_cron_data.xml',
        'report/report_employee_template.xml',
    ],
    'installable': True,
    'auto_install': False
}
