# -*- coding: utf-8 -*-
{
    'name': "Grimm Web Editor",

    'summary': """
        Grimm HTML Web Editor customizations""",

    'author': "Viet Pham, Grimm Gastronomiebedarf GmbH",
    'website': "https://www.grimm-gastrobedarf.de",
    'description': """By default, the HTML editor leaves a new item when we press enter and type nothing while keeping 
    the list mode on. This module avoids adding an extra item if we type nothing.""",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Hidden',
    'version': '0.1.0',

    # any module necessary for this one to work correctly
    'depends': ['web_editor'],

    # always loaded
    'data': ['templates.xml'],
}
