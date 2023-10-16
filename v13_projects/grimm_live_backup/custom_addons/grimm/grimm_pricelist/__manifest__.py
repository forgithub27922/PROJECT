# -*- coding: utf-8 -*-

{
    'name': 'Grimm Pricelist',
    'version': '0.1.0',
    'author': 'Viet Pham, GRIMM Gastronomiebedarf GmbH',
    'summary': 'Grimm Price List',
    'website': 'https://www.grimm-gastrobedarf.de/',
    'category': 'Sales',
    'depends': ['product', 'sale', 'purchase', 'asset_base', 'grimm_product', 'grimm_crm'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_view.xml',
        'views/pricelist_view.xml',
        'views/product_view.xml',
        'views/product_price_history_view.xml',
        'views/product_price_group_view.xml',
        'views/sale_config_views.xml',
        'data/data.xml',
    ],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
