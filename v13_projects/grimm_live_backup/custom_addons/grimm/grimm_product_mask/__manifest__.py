{
    'name': 'GRIMM Product Mask',
    'version': '0.1',
    'application': False,
    'author': 'Karthik Pradhan, Grimm Gastronomiebedarf GmbH',
    'website': 'https://grimm-gastrobedarf.de',
    #~ 'license': 'LGPL-3',
    'category': 'UI/UX',
    'summary': 'Products',
    'description': """
        A new view for products.
    """,
    'depends': ['base', 'sale', 'of_base_magento_extensions_v9', 'web'],
    'data': [
        'security/security.xml',
        'views/product_view.xml',
    ],
    'installable': True,
    'qweb': [],
}