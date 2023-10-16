# -*- encoding: utf-8 -*-
##############################################################################
#
#    Skyscend Business Solutions
#    Copyright (C) 2019 (http://www.skyscendbs.com)
#
##############################################################################
{
    'name': 'Automatic User Creation from Employee and Access based on Job Position',
    'version': '13.0.0.1',
    'category': 'HR',
    'license': 'AGPL-3',
    'description': """
    When creating employees the User should be automatically created.
    This user will have the access rights as per the Job Position assigned in Employee.
    """,
    'author': 'Skyscend Business Solutions',
    'website': 'http://www.skyscendbs.com',
    'depends': ['hr', 'contacts'],
    'data': [
        'views/res_config_view.xml',
        'views/hr_view.xml',
        'data/employee_credential_template.xml',
        'views/res_partner_view.xml'
    ],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'auto_install': False
}
