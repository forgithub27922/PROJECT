# -*- coding: utf-8 -*-
{
    'name': "Sms Transport",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Syncology",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr', 'fleet','sms_core', 'sky_hr_recruitment_custom', 'web'],

    # always loaded
    'data': [
        'security/sms_transport_groups.xml',
        'security/ir.model.access.csv',
        'views/res_config_settings_view.xml',
        'views/sms_transport_view.xml',
        'wizard/transport_schedule_report_wizard.xml',
        'wizard/transport_complaint_resolved_wizard.xml',
        'report/report_transport_schedule.xml',
        'report/reports_declarator.xml',
        'views/fleet_view.xml',
        'views/sms_transport_menu.xml',
        'views/assets.xml',

    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
