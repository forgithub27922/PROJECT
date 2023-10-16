# -*- coding: utf-8 -*-
{
    'name': "udm_permitidas_yeidala",
    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",
    'description': """
        Long description of module's purpose
    """,
    'author': "Yeidala",
    'website': "http://www.yeidala.com",
    'category': 'Uncategorized',
    'version': '1.4',
    'depends': ['base_setup', 'product', 'purchase', 'purchase_request', 'stock', 'purchase_stock'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/product_template_views.xml',
    ]
}
