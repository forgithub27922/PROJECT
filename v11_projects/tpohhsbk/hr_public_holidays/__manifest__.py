# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'HR Public Holidays',
    'version': '1.0',
    'category': 'Human Resources',
    'author': 'Bista Solutions Pvt. Ltd.',
    'website': 'http://www.bistasolutions.com',
    'depends': ['hr_holidays', 'bista_hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_public_holidays_view.xml',
    ],
    'installable': True,
}
