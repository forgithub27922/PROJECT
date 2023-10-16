# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2016 Openfellas (http://openfellas.com) All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly advised to contract support@openfellas.com
#
###############################################################################


{
    'name': 'Grimm Extensions',
    'version': '1.0',
    'author': 'openfellas, Viet Pham, Grimm Gastronomiebedarf GmbH',
    'summary': 'Grimm',
    'website': 'http://openfellas.com',
    'description': "Grimm Extensions module",
    'category': 'Uncategorized',
    'depends': [
        #'mro_base',
        'sale',
        'asset_base',
        'sale_exception',
        'sale_timesheet',
        'stock',
        'delivery',
        'sale_subscription',
        'purchase',
        'project',
        'crm_claim',
        'repair',
        'product',
        'grimm_product',
        'mail',
        'account',
        'web_m2x_options',
        'account_payment_sale',
        #'mass_editing',
        #'grimm_reports',
    ],
    'data': [
        'data/sale_contract.xml',
        'data/mro_order_create_cron.xml',
        'data/data.xml',
        'data/claim_mail_template.xml',
        'data/remove_odoo_email.xml',
        'data/crmclaimseq.xml',
        'data/task_seq.xml',
        'views/ir_qweb.xml',
        'views/sale_order_view.xml',
        'views/sale_contract_view.xml',
        'views/asset_asset_view.xml',
        'views/stock_view.xml',
        'views/crm_claim_view.xml',
        'wizard/project_task_delegate_view.xml',
        'wizard/import_products_view.xml',
        'views/project_task_view.xml',
        # 'views/mro_order_view.xml',
        # 'views/mrp_repair_view.xml',
        'views/product_view.xml',
        'views/account_invoice_view.xml',
        'views/product_attrib_set_view.xml',
        'views/purchase.xml',
        'views/res_partner.xml',
        'views/sale_layout_category_view.xml',
        # 'security/security.xml',
        'security/ir.model.access.csv'
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'sequence': 110
}
