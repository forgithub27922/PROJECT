# -*- coding: utf-8 -*-

{
    'name': 'GRIMM Service Scan',
    'version': '13.0.1',
    'application': True,
    'author': 'Karthik Pradhan, Grimm Gastronomiebedarf GmbH',
    'website': 'https://grimm-gastrobedarf.de',
    #~ 'license': 'LGPL-3',
    'category': 'Mobile',
    'summary': 'Grimm Barcode',
    'description': """
        Main purpose of this module is to scan the barcodes and store it in the respective models.
    """,
    'depends': ['base', 'sale', 'project', 'stock_barcode', 'grimm_extensions'],
    'data': [
        'security/security.xml',
        'views/scan_barcode.xml',
        'views/scan_barcode_app.xml',
        'views/task_view.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'qweb': [
        "static/src/xml/scan_barcode.xml",
    ],
}
