# -*- coding: utf-8 -*-
{
    'name': "Reporte Resumen Inventario",
    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",
    'description': """
        Long description of module's purpose
    """,
    'author': "Yeidala",
    'website': "http://odoo.yeidala.com",
    'category': 'Uncategorized',
    'version': '1.6',
    'depends': ['base_setup', 'stock', 'purchase', 'stocktransfer_accountmove_yeidala', 'report_xlsx'],
    'data': [
        'security/ir.model.access.csv',
        'views/inventory_report_views.xml',
        # 'views/templates.xml',
    ],
}
