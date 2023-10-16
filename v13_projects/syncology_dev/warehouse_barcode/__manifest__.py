##########################################################################################
#
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#    Copyright (C) 2020 Skyscend Business Solutions Pvt. Ltd. (http://www.skyscendbs.com)
#
##########################################################################################
{
    'name': 'Warehouse Barcode',
    'version': '13.0.0.1',
    'category': 'stock',
    'license': 'AGPL-3',
    'description': """
    This module is used scan barcodes on the Warehouse Order
    """,
    'author': 'Skyscend Business Solutions Pvt. Ltd.',
    'website': 'http://www.skyscendbs.com',
    'depends': ['stock', 'barcodes'],
    'data': [
        'views/stock_picking.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True
}
