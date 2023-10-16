##########################################################################################
#
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#    Copyright (C) 2020 Skyscend Business Solutions Pvt. Ltd. (http://www.skyscendbs.com)
#
##########################################################################################
{
    'name': 'Sky Stock Custom',
    'version': '13.0.0.1',
    'category': 'product',
    'description': """
    This module is used scan barcodes on the Product Create and Update
    """,
    'author': 'Skyscend Business Solutions Pvt. Ltd.',
    'website': 'http://www.skyscendbs.com',
    'depends': ['product', 'barcodes'],
    'data': [
        'views/product_template_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}