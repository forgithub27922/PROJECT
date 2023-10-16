{
    'name': 'GRIMM UI',
    'version': '0.1',
    'application': False,
    'author': 'Karthik Pradhan, GRIMM Gastrobedarf',
    'website': 'https://grimm-gastrobedarf.de',
    #~ 'license': 'LGPL-3',
    'category': 'Reporting',
    'summary': 'Grimm Tools',
    'description': """
        This module enhances the UI of the Odoo backend as well as frontend.
        1. Enhances product form view with image viewer and removes horizontal separator
        2. Removes language selector dropdown & Odoo brand promotion from website
    """,
    'depends': ['base', 'web', 'website', 'product', 'web_widget_open_tab'],
    'data': [
        'templates/templates.xml',
        'templates/website_extend.xml',
        'views/product.xml',
    ],
    'installable': True,
    'qweb': [
        'static/src/xml/360_deg_widget.xml'
    ],
}
