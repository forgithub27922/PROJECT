# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Bista Web M2O Non-Clickable',
    'version': '1.1',
    'category': 'Web',
    'description': """
            This module removes the click functionality on many2one field.
                   """,
    'author': 'Bista Solutions Pvt.Ltd.',
    'website': 'https://www.bistasolutions.com/',
    'depends': ['web'],
    'data': [
        'views/templates.xml',
    ],
    'qweb': [
        "static/src/xml/base_extend.xml",
    ],
    'installable': True,
}
