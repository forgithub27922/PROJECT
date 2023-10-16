# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'HR Gratuity Extended',
    'version': '1.1',
    'category': 'Human Resources',
    'summary': 'Calculating the gratuity for employee as per UAE Rule.',
    'description': """
Bista HR Gratuity
====================
* Configuration gratuity (Payroll / Configuration / Gratuity).
    """,
    'author': 'Bista Solutions Pvt. Ltd.',
    'website': 'http://www.bistasolutions.com',
    'depends': ['bista_hr_gratuity'],
    'data': [
        'security/ir.model.access.csv',
        'data/gratuity_data.xml',
        'data/ir_cron.xml',
        'views/hr_gratuity_view.xml',
    ],
    'installable': True,
}
