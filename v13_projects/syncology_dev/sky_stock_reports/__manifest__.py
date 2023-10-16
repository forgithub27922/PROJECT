# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#
##############################################################################
{
    'name': 'Product Movement Report',
    'version': '13.0.0.1',
    'category': 'Product',
    'description': """
    Daily Operation of a Warehouse
    """,
    'author': 'Skyscend Business Solutions',
    'website': 'http://www.skyscendbs.com',
    'depends': ['product', 'stock'],
    'data': [
        'views/product_movement_wizard.xml',
    ],
    'installable': True,
    'auto_install': False
}