{
    'name': 'Sky Stock Account',
    'version': '13.0.0.1',
    'description': """
    """,
    'author': 'Skyscend Business Solutions',
    'website': 'http://www.skyscendbs.com',
    'depends': ['base', 'stock', 'account', 'sky_stock_sms_custom'],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_picking_views.xml',
    ],
    'installable': True,
    'auto_install': False
}
