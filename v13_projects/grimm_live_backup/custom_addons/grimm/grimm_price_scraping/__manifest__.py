{
    'name': 'GRIMM Price Scraping',
    'version': '0.1',
    'application': False,
    'author': 'Dipak Suthar',
    'website': 'https://grimm-gastrobedarf.de',
    #~ 'license': 'LGPL-3',
    'category': 'Product Pricing',
    'summary': 'Scrap the price from cloud',
    'description': """
        This module provide functionality for scraping price from different sources.
    """,
    'depends': ['base', 'sale'],
    'data': [
        'view/product_view.xml',
    ],
    "qweb": [
            'static/src/xml/advance_tooltip.xml',
        ],
    'installable': True
}