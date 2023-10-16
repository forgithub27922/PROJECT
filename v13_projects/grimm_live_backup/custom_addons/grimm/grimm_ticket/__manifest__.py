# -*- coding: utf-8 -*-
{
    'name': 'Grimm Ticket',
    'version': '0.1.0',
    'author': 'Bitlane',
    'summary': 'Grimm Ticket System',
    'website': 'https://bitlane.net/',
    'category': 'Uncategorized',
    'depends': ['mail', 'hr'],
    'data': [
        'security/security.xml',
        # 'security/grimm_ticket_access_rules.xml',
        'security/ir.model.access.csv',
        'data/grimm_ticket_sequence.xml',
        'data/grimm_ticket_stage.xml',
        'wizards/grimm_ticket_assign_wizard_view.xml',
        'views/grimm_ticket_assets.xml',
        'views/grimm_ticket_views.xml',
        'views/grimm_ticket_menu.xml',

        'views/hr_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,

    'qweb': [],
}
