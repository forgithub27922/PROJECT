# -*- coding: utf-8 -*-


{
    'name': 'Grimm Reports',
    'version': '13.0.1.0.0',
    'author': 'openfellas, Viet Pham, GRIMM Gastronomiebedarf GmbH',
    'summary': 'Grimm Custom Addons',
    'website': 'http://openfellas.com',
    'description': "Grimm extended reports",
    'category': 'Uncategorized',
    'depends': ['web',
                'base',
                'mail',
                'product',
                'hr',
                'connector_magento',
                'survey',
                'sale',
                'stock',
                'analytic',
                'hr_timesheet', ],
    'data': [
        'security/ir.model.access.csv',
        'view/css.xml',
        'view/layouts.xml',
        'view/report_customer_user.xml',
        'view/report_saleorder_grimm.xml',
        'view/report_invoice_grimm.xml',
        'view/report_delivery_grimm.xml',
        'view/report_purchase_grimm.xml',
        'view/report_quotation_grimm.xml',
        'view/report_delivery_notice_grimm.xml',
        'view/report_project_description_grimm.xml',
        'view/report_claim_warranty.xml',
        'view/report_claim_warranty.xml',
        'view/report_stockinventory.xml',
        'view/report_stockinventory_signature.xml',
        'view/report_stock_valuation.xml',
        'view/report_service_order.xml',
        'view/report_proforma_grimm.xml',
        'view/report_wartungsauftrag_grimm.xml',
        'view/report_service_begleitschein_grimm.xml',
        'view/reports.xml',
        'data/delivery_notice_mail.xml',
        'view/replace_default_button.xml',
        'view/sale_view.xml',
        'view/account_invoice_view.xml',
        'view/purchase_order_view.xml',
        'view/stock_picking_view.xml',
        'view/res_company_view.xml',
        'data/data_claim_mail.xml',
        'data/proforma_mail_template.xml',
    ],
    'demo': [],
    'qweb': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
