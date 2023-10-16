# -*- coding: utf-8 -*-
{
    'name': 'Bista HR Lifecycle',
    'version': '1.0',
    'website': '',
    'category': 'hr',
    'depends': ['bista_hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_employee_view.xml',
        'wizard/hr_lifecycle_wizard_view.xml',
        'data/employee_status_update.xml',
    ],
    'installable': True,
    'auto_install': False,
}
