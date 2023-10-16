# -*- coding: utf-8 -*-

{
    'name': 'Grimm Asset Base module',
    'version': '1.0',
    'author': 'openfellas, upgraded to Odoo 11 by Viet Pham - Grimm Gastronomiebedarf GmbH',
    'summary': 'Grimm',
    'website': 'https://www.grimm-gastronomiebedarf.de',
    'description': "Grimm Asset Base module",
    'category': 'Uncategorized',
    'depends': ['web', 'base', 'mail', 'product', 'hr', 'stock', 'survey', 'sale_subscription'],
    'data': [
        'data/asset_seq.xml',
        'security/ir.model.access.csv',
        'security/asset_security_view.xml',
        'wizard/change_partners_wizard_view.xml',
        'views/grimm_menu.xml',
        'views/asset_asset_view.xml',
        'views/asset_facility_view.xml',
        'views/product_view.xml',
        'views/product_brand.xml',
        'views/res_partner.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
