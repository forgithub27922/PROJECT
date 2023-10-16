# -*- coding: utf-8 -*-
{
    'name': "Maintenance Stage Track",
    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",
    'description': """
        Long description of module's purpose
    """,
    'author': "Yeidala",
    'website': "https://yeidala.odoo.com",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base_setup', 'maintenance'],
    'data': [
        'security/ir.model.access.csv',
        'views/maintenance_stage_track_views.xml',
    ]
}

# maintenance.stage.track
