##########################################################################################
#
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#    Copyright (C) 2020 Skyscend Business Solutions Pvt. Ltd. (http://www.skyscendbs.com)
#
##########################################################################################
{
    'name': 'Product Barcode',
    'version': '13.0.0.1',
    'category': 'stock',
    'description': """
    This module is used scan barcodes on wizard
    """,
    'author': 'Skyscend Business Solutions Pvt. Ltd.',
    'website': 'http://www.skyscendbs.com',
    'depends': ['barcodes', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/product_barcode_wiz_view.xml',
        'views/assets.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}
