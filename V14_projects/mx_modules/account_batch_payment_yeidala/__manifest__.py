# -*- coding: utf-8 -*-
{
    'name': "Batch Payment Yeidala",
    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",
    'description': """
        Long description of module's purpose
    """,
    'author': "Yeidala",
    'website': "http://yeidala.com",
    'category': 'Accounting/Accounting',
    'version': '1.8',
    'depends': ['account_batch_payment'],
    'data': [
        # 'security/ir.model.access.csv',
        'data/account_batch_payment_data.xml',
        'views/account_journal_views.xml',
        # 'views/templates.xml',
    ],
}
