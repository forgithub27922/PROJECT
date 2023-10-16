# -*- coding: utf-8 -*-
{
    'name': "Grimm Delivery",

    'summary': """
        Grimm delivery customizations""",

    'author': "Bitlane",
    'website': "https://bitlane.net",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Stock',
    'version': '0.1.0',

    # any module necessary for this one to work correctly
    'depends': ['sale_stock', 'delivery', 'grimm_magentoerpconnect'],

    # always loaded
    'data': [
        'views/product_view.xml',
        'security/ir.model.access.csv'
    ],
}
