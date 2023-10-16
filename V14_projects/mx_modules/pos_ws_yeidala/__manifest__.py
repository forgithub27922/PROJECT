# -*- coding: utf-8 -*-
{
    'name': "POS ",
    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",
    'description': """
        Long description of module's purpose
    """,
    'author': "Yeidala",
    'website': "http://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '1.13',
    'depends': ['base_setup', 'point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/point_of_sale_views.xml',
        'data/ir_cron_data.xml'
    ]
}
