# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name' : 'Dynamic Mail',
    'version' : '1.0',
    'description': """ 
    """,
    'depends' : ['base','mail'],
    'data': [
            'security/ir.model.access.csv',
            'security/security.xml',
            'views/dynamic_mail.xml',
    ],
    'author': 'Bista Solutions Pvt. Ltd.',
    'website': 'http://www.bistasolutions.com',
    'installable': True,
    'application': True,
}
