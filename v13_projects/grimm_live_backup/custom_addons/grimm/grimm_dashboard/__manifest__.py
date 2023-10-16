# -*- coding: utf-8 -*-

{
    'name': 'GRIMM Dashboard',
    'version': '0.1',
    'application': False,
    'author': 'Karthik Pradhan, Grimm Gastronomiebedarf GmbH',
    'website': 'https://grimm-gastrobedarf.de',
    #~ 'license': 'LGPL-3',
    'category': 'Reporting',
    'summary': 'Grimm Dashboard',
    'description': """
        As the name suggests, this module displays dashboards on specific models (CRM, etc.,).
    """,
    'depends': ['base', 'crm', 'sale', 'sale_margin', 'mass_mailing', 'web_enterprise'],
    'data': [
        # 'views/crm_profit.xml',
        'static/src/xml/assets.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/cost_data.xml',
    ],
    'installable': True,
    'qweb': [
        "static/src/xml/app_drawer.xml",
    ],
}
