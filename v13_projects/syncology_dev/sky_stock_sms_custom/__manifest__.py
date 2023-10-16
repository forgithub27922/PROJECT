{
    'name': 'Stock Sms Custom',
    'version': '13.0.0.1',
    'description': """
    This module is used for Contacts & Addresses in the transfer.
    """,
    'author': 'Skyscend Business Solutions Pvt. Ltd.',
    'website': 'http://www.skyscendbs.com',
    'depends': ['sky_hr_custom', 'sms_core', 'stock'],
    'data': [
        'views/stock_picking_views.xml',
        'views/stock_warehouse_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}
