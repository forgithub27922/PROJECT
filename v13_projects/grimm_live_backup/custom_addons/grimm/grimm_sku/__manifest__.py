# -*- coding: utf-8 -*-

{
    'name': 'GRIMM SKU',
    'version': '13.0.1',
    'application': False,
    'author': 'Karthik Pradhan',
    'website': 'https://grimm-gastrobedarf.de',
    #~ 'license': 'LGPL-3',
    'category': 'Reporting',
    'summary': 'Grimm Tools',
    'description': """
        Main purpose of this module is to fetch the information about the spare part from website(s), database(s), etc.
        The fetching of information is done separately with a Python script and this module creates the table and fetch the information from those tables.
    """,
    'depends': ['base', 'product', 'of_base_magento_extensions_v9'],
    'data': [
        'security/ir.model.access.csv',
        'views/sku_mapping.xml',
        'wizards/prompt_attribute_dialog.xml',
        'wizards/scrape_sparepart_dialog.xml',
        'wizards/prompt_sku_exists.xml',
        'wizards/prompt_attribute_exists.xml',
    ],
    'installable': True,
    'qweb': [],
}
