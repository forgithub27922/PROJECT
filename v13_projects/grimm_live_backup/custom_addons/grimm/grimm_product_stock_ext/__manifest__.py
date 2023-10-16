{
    'name': 'GRIMM Product and Stock Extension',
    'version': '0.1',
    'application': False,
    'author': 'Karthik Pradhan',
    'website': 'https://grimm-gastrobedarf.de',
    #~ 'license': 'LGPL-3',
    'category': 'Product',
    'summary': 'Relaces weight field with onhand_qty',
    'description': """
        This module provides product and stock related enhancements.
        1. Adds validation on stock.picking
        2. Adds forecast_triplet field on product.template
    """,
    'depends': ['base', 'grimm_magentoerpconnect', 'product', 'sale', 'web_widget_open_tab'],
    'data': [
        'view/onhand_qty.xml',
        'view/tooltip_assets.xml',
        # 'view/product_view.xml',
        # 'security/ir.model.access.csv',
    ],
    "qweb": [
            'static/src/xml/advance_tooltip.xml',
        ],
    'installable': True
}