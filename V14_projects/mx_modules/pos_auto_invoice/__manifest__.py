# -*- coding: utf-8 -*-
{
    'name': "POS Auto Invoice",
    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",
    'description': """
        Long description of module's purpose
    """,
    'author': "Yeidala",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '1.4',
    'depends': ['base_setup', 'point_of_sale', 'account'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/pos_auto_invoice_views.xml'
    ]
}
