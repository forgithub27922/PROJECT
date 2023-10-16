# -*- coding: utf-8 -*-

{
    'name': 'GRIMM Modifications',
    'version': '13.0.1',
    'application': False,
    'author': 'Karthik Pradhan, Grimm Gastrobedarf.de',
    'website': 'https://grimm-gastrobedarf.de',
    #~ 'license': 'LGPL-3',
    'category': 'Reporting',
    'summary': 'Grimm Tools',
    'description': """
        Main purpose of this module is to do modifications tailored to staffs' needs.
        1. Multi-company email support
        2. Inventory Development Report
        3. Purchase Report
        4. Available locations dialog box on stock.picking
        5. Contact address handling extension
        6. Line numbers on Invoice & Purchase reports
        7. Adds track_visibility to pricelist item fields
    """,
    'depends': [
        'stock', 'hr', 'mail_multicompany', 'fleet', 'shopware_connector', 'base_location', 'grimm_pricelist', 'product_bundle_pack'],
    'data': [
        'views/pricelist_item.xml',
        'views/backend.xml',
        'views/hr_module_inherit.xml',
        'views/helpdesk.xml',
        'views/inventory_product.xml',
        'views/email_template.xml',
        'data/multi_comp_email.xml',
        'views/purchase_report.xml',
        'views/fleet.xml',
        'views/res_partner.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/helpdesk.xml',
        'views/cron_jobs.xml',
        'views/sale_purchase_bill.xml',
        'views/inventory_report.xml',
        'views/stock.xml',
    ],
    'installable': True,
    'qweb': [],
}
