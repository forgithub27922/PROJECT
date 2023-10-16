# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#
##############################################################################
{
    'name': 'Timeoff Custom',
    'version': '13.0.0.1',
    'category': 'HR',
    'description': """
    This module is used add leave type in hr holidays
    """,
    'author': 'Skyscend Business Solutions',
    'website': 'http://www.skyscendbs.com',
    'depends': ['sky_hr_recruitment_custom','hr_holidays'],
    'data': [
        'security/hr_timeoff_security.xml',
        'security/ir.model.access.csv',
        'views/hr_leave_view.xml',
        'views/hr_leave_type_view.xml',
        'views/hr_leave_allocation_view.xml',
        'data/leaves_allocation_scheduler.xml',
        'views/reject_request_wizard_view.xml',
        'views/hr_employee_view.xml',
        'views/update_leave_vacation_balance_wizard_view.xml',
        'views/update_multi_leave_vacation_balance_wizard_view.xml',
    ],
    'installable': True,
    'auto_install': False
}