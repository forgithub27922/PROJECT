# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Bista HR Experience',
    'version': '1.0',
    'category': 'Human Resources',
    'summary': 'HR Experience',
    'description': """
            This Module Contains Experience of Employee.
                   """,
    'author': 'Bista Solutions Pvt. Ltd.',
    'website': 'https://www.bistasolutions.com/',
    'depends': ['bista_hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_employee_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
