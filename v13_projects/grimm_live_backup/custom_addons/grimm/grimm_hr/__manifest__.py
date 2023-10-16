{
    'name': 'GRIMM HR Extension',
    'version': '0.1',
    'application': False,
    'author': 'Dipak Suthar, GRIMM Gastrobedarf',
    'website': 'https://grimm-gastrobedarf.de',
    #~ 'license': 'LGPL-3',
    'category': 'Reporting',
    'summary': 'Grimm HR Extension',
    'description': """
        This module enhances odoo HR Application.
    """,
    'depends': ['base', 'web', 'hr', 'hr_holidays', 'hr_holidays_calendar'],
    'data': [
        'data/data.xml',
        'views/hr_view.xml',
        'security/ir.model.access.csv'
    ],
    'installable': True,
}
