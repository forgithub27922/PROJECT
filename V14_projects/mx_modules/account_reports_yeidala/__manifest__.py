# -*- coding: utf-8 -*-
{
    'name': "Account Reports Yeidala",
    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",
    'description': """
        Long description of module's purpose
    """,
    'author': "Yeidala",
    'website': "https://odoo.yeidala.com/",
    'category': 'Uncategorized',
    'version': '1.4',
    'depends': ['account', 'account_reports'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/account_reports.xml',
        # 'views/templates.xml',
    ]
}
