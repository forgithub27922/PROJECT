# -*- coding: utf-8 -*-
{
    'name': "Factura Global",

    'summary': """
        Factura de pedidos del pos o ventas en un periodo determinado""",

    'description': """
        Genera una factura borrador de pedidos de pos o ventas que no tengan asociada una factura
    """,

    'author': "silvau",
    'website': "http://www.zeval.com.mx",

    'category': 'account',
    'version': '13.1',
    'depends': ['account','sale','point_of_sale','l10n_mx_edi'],

    'data': [
        'data/cfdi_factura_global.xml',
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/account_invoice_view.xml',
        'views/product_view.xml',
        'views/pos_payment_method_view.xml',
        'views/res_config_settings_view.xml',
        'views/pos_session_view.xml',
        'wizard/factura_global_view.xml',
    ],
    'post_init_hook': 'post_init_hook',
}
