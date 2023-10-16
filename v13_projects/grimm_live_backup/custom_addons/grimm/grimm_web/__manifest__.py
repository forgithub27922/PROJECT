# -*- coding: utf-8 -*-
{
    'name': "Grimm Web",
    'summary': """Web Extension for Grimm""",
    'author': "Karthik Pradhan, Grimm Gastronomiebedarf GmbH",
    'website': "https://www.grimm-gastrobedarf.de",
    'category': 'Hidden',
    'description': """
            This module enhances the UI of the Odoo backend.
            1. Pushes the chatter in the form view down except for account.move forms
            2. Extends Document Viewer to .eml & .csv filetypes
        """,
    'version': '13.0.1.0',
    'depends': ['web', 'web_enterprise'],
    'data': ['templates/assets.xml'],
    'qweb': ['static/src/xml/preview.xml'],
}
