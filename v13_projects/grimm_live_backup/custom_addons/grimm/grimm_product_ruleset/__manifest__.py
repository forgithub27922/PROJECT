# -*- coding: utf-8 -*-

{
    'name': 'GRIMM Product Ruleset',
    'version': '0.1',
    'application': False,
    'author': 'Karthik Pradhan',
    'website': 'https://grimm-gastrobedarf.de',
    #~ 'license': 'LGPL-3',
    'category': 'Reporting',
    'summary': 'Grimm Tools',
    'description': """
        Main purpose of this module is to enhance naming of product by defining rulesets.
    """,
    'depends': ['base', 'sale', 'grimm_shopware6_connector', 'grimm_extensions', 'of_base_magento_extensions_v9', 'grimm_product', 'shopware_connector'],
    'data': [
        # 'views/product_view.xml',
        'views/product_ruleset.xml',
        'views/propertyset_wizard.xml',
        'security/ir.model.access.csv',
        'views/shopware_ruleset.xml',
    ],
    'installable': True,
    'qweb': [],
}
