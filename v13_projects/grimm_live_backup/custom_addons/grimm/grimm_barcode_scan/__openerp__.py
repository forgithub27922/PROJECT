# -*- coding: utf-8 -*-
{
    'name': 'Grimm Barcode Scan',
    'version': '0.1.0',
    'author': 'Dipak Suthar',
    'summary': 'Grimm enhancement for Barcode scanning',
    'website': 'https://grimm-gastrobedarf.de/',
    'category': 'web',
    'depends': [
        'web',
        'base',
        'stock_barcode'
        #'grimm_tools'
    ],
    'data': [
        'views/user_view.xml',
        'views/grimm_web_assets.xml',
        'views/picking_report.xml',
        'views/product_label_report_print.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,

    'qweb': [
        'static/src/xml/photo_barcode.xml',
        'static/src/xml/stock_locations.xml'
    ],
}
