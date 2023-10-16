# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (C) Skyscend Business Solutions
#    Copyright (C) Skyscend Business Solutions Pvt. Ltd.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Time Tracking',
    'version': '13.0.0.1',
    'category': 'HR',
    'description': """
    This module is used to track the time of the employee
    """,
    'author': 'Skyscend Business Solutions Pvt. Ltd.',
    'website': 'http://www.skyscendbs.com',
    'depends': ['hr_attendance', 'sky_hr_attendance_custom'],
    'data': [
        'security/hr_time_tracking_security.xml',
        'security/ir.model.access.csv',
        'views/hr_employee_view.xml',
        'views/working_schedule_wiz_view.xml',
        'views/time_tracking_view.xml',
        'data/ir_cron_data.xml',
        'views/emp_working_days_report_wiz_view.xml',
        'views/update_working_schedule_wiz_view.xml',
        'views/update_working_schedule_employee_wiz_view.xml',

    ],
    'installable': True,
    'auto_install': False
}