# -*- encoding: utf-8 -*-
##############################################################################
#
#    Skyscend Business Solutions
#    Copyright (C) 2019 (http://www.skyscendbs.com)
#
##############################################################################
{
    'name': 'Time Tracking Holidays',
    'version': '13.0.0.1',
    'category': 'HR',
    'description': """
    This module will check the Hr Time Tracking Line while generating the tracking
    """,
    'author': 'Skyscend Business Solutions',
    'website': 'http://www.skyscendbs.com',
    'depends': [
        'sky_hr_time_tracking',
        'sky_hr_timeoff_custom',
        'sky_hr_public_holidays_time_tracking',
    ],
    'data': [
        'views/time_tracking_view.xml',
    ],
    'installable': True,
    'auto_install': False
}
