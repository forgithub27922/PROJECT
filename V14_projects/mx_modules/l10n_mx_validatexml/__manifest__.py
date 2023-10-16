# -*- coding: utf-8 -*-
{
    'name': "Validar XML",
    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",
    'description': """
        Long description of module's purpose
    """,
    'author': "Yeidala",
    'website': "https://www.odoo.com/es_ES/partners/yeidala-1234306",
    'category': 'Uncategorized',
    'version': '1.19',
    'depends': ['account', 'l10n_mx_edi'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/validaxml_views.xml',
        # 'views/templates.xml',
    ],
}
