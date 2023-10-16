# -*- coding: utf-8 -*-
{
    'name': "Analytic Users Yeidala",
    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",
    'description': """
        Long description of module's purpose
    """,
    'author': "Yeidala",
    'website': "https://yeidala.odoo.com",
    'category': 'Uncategorized',
    'version': '1.9',
    'depends': ['base', 'purchase', 'purchase_stock', 'sale', 'maintenance', 'mrp', 'stocktransfer_accountmove_yeidala'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/res_users_views.xml',
        'views/account_move_line_views.xml',
        'views/purchase_order_views.xml',
        'views/sale_order_line_views.xml',
        'views/maintenance_views.xml',
        'views/mrp_production_views.xml',
        # 'views/templates.xml',
    ]
}
