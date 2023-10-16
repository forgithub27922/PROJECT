{
    'name': 'Sky School Company',
    'version': '13.0.0.1',
    'description': """
    This module is used for replacing company string to school""",
    'author': 'Skyscend Business Solutions',
    'website': 'http://www.skyscendbs.com',
    'depends': ['base', 'hr', 'sms_transport'],
    'data': [
        'security/base_groups.xml',
        'views/ir_attachment_views.xml',
        'views/hr_employee_views.xml',
        'views/fleet_view.xml',
        'views/base_menus.xml',
    ],
    'installable': True,
    'auto_install': False
}
