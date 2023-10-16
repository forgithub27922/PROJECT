{
    'name': 'Stock Hr Custom',
    'version': '13.0.0.1',
    'description': """
    This module is used for create employee handover throw transfer of inventory.
    """,
    'author': 'Skyscend Business Solutions Pvt. Ltd.',
    'website': 'http://www.skyscendbs.com',
    'depends': ['sky_stock_sms_custom'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_employee_views.xml',
        'views/stock_equipment_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}