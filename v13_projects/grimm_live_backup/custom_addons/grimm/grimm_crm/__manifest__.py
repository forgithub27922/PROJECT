# -*- coding: utf-8 -*-

{
    'name': 'Grimm CRM',
    'version': '0.3.0',
    'author': 'Viet Pham',
    'summary': 'Grimm customer relationship management',
    'website': 'https://www.grimm-gastrobedarf.de/',
    'category': 'Sales',
    'depends': ['crm', 'crm_claim', 'sale', 'calendar', 'project', 'mail', 'sale_crm'],
    'data': [
        'data/crm_stage_data.xml',
        'views/crm_lead_view.xml',
        'views/crm_claim_view.xml',
        'views/project_task_view.xml',
        'views/calendar_event_view.xml',
        'views/sale_order_view.xml',
        'wizards/mail_compose_message_view.xml',
        # 'views/mail_templates.xml',
        'views/mail_template_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,

    'qweb': [],
}
