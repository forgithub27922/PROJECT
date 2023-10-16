# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#
##############################################################################
{
    'name': 'Website Recruitment Custom',
    'version': '13.0.0.1',
    'category': 'HR',
    'description': """
    This module is used add fields and process on recruitment
    """,
    'author': 'Skyscend Business Solutions',
    'website': 'http://www.skyscendbs.com',
    'depends': ['website_hr_recruitment', 'sky_hr_recruitment_custom', 'website_form'],
    'data': [
        'views/assets.xml',
        'views/website_hr_recruitment_templates.xml',
        'views/hr.xml',
    ],
    'installable': True,
    'auto_install': False
}