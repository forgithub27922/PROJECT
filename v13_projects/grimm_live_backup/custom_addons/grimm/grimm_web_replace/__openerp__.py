# -*- coding: utf-8 -*-
{
    'name': 'Grimm Web Replace',
    'version': '0.1.0',
    'author': 'Dipak Suthar',
    'summary': 'Grimm Web view replacement',
    'website': 'https://grimm-gastrobedarf.de/',
    'category': 'web',
    'depends': ['web', 'base'],
    'data': [
        'views/grimm_web_layout.xml',
        #'views/grimm_web_assets.xml',
        'views/user_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,

    'qweb': [],
}
