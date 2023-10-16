# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#    Copyright (C) 2020 Skyscend Business Solutions Pvt. Ltd.(http://www.skyscendbs.com)
#
##############################################################################
{
    'name': 'Public Holidays',
    'version': '13.0.0.1',
    'category': 'HR',
    'description': """
    This module is adds public holidays feature""",
    'author': 'Skyscend Business Solutions Pvt. Ltd.',
    'website': 'http://www.skyscendbs.com',
    'depends': ['sky_hr_timeoff_custom'],
    'data': [
        'security/hr_public_holidays_security.xml',
        'security/ir.model.access.csv',
        'views/hr_public_holidays_view.xml',
    ],
    'installable': True,
    'auto_install': False
}
