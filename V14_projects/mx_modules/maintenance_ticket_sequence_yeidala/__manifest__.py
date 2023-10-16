# -*- coding: utf-8 -*-
{
    'name': "Maintenance Ticket Sequence Yeidala",
    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",
    'description': """
        Long description of module's purpose
    """,
    'author': "Yeidala",
    'website': "http://www.yeidala.com",
    'category': 'Uncategorized',
    'version': '1.2',
    'depends': ['maintenance'],
    'data': [
        # 'security/ir.model.access.csv',
        'data/maintenance_request_data.xml',
        'views/maintenance_request_views.xml',
    ]
}
