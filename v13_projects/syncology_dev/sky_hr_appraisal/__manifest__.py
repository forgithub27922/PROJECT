# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#
##############################################################################
{
    'name': 'Appraisal',
    'version': '13.0.0.1',
    'category': 'HR',
    'description': """
    This module is used to Create Performance Appraisal Mechanism""",
    'author': 'Skyscend Business Solutions',
    'website': 'http://www.skyscendbs.com',
    'depends': ['sky_hr_custom'],
    'data': [
        'security/hr_appraisal_security.xml',
        'security/ir.model.access.csv',
        'views/hr_kra_view.xml',
        'views/hr_department_view.xml',
        'views/hr_employee_appraisal_view.xml',
        'views/generate_appraisal_wiz_view.xml',
        'views/hr_employee_view.xml',
    ],
    'installable': True,
    'auto_install': False
}
