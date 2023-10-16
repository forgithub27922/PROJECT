# -*- coding: utf-8 -*-

{
    'name': 'GRIMM Enhancements',
    'version': '0.1',
    'application': False,
    'author': 'Karthik Pradhan, Grimm Gastronomiebedarf GmbH',
    'website': 'https://grimm-gastrobedarf.de',
    #~ 'license': 'LGPL-3',
    'category': 'Reporting',
    'summary': 'Grimm Tools',
    'description': """
        1. Creates a link to purchase order from Accounting referring to Source Document field.
        2. This module avoids overwriting the expiration_date column in our database.
        3. Displays a message in case the password is expired, and also notifies the user upon log in if the password is
        expiring soon so that the user can change their password.
    """,
    'depends': ['base', 'sale', 'account', 'delivery', 'web', 'account_3way_match', 'password_security', 'base_geolocalize', 'maintenance'],
    'data': [
        'security/security_view.xml',
        'views/account.xml',
        'views/res_partner.xml',
        'views/maintenance_view.xml'
        # 'wizards/address_validation_wizard.xml'
    ],
    'installable': True,
    'qweb': [],
}
