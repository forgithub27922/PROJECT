# -*- coding: utf-8 -*-
{
    'name': "bfiskur_yeidala",
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
    'depends': ['account', 'l10n_mx_edi'],
    'data': [
        'security/ir.model.access.csv',
        'data/bfiskur_data.xml',
        'data/ir_cron.xml',
        'views/account_invoice_views.xml',
        'views/res_config_settings_view.xml',
        'wizard/bfiskur_wiz_views.xml'
        # 'views/templates.xml',
    ],
}
