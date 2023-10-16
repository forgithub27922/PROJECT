# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Bista Analytic Account',
    'version': '1.0',
    'author': 'Bista Solutions',
    'sequence': 11,
    'category': 'Accounting',
    'description': """
Analytic Account
=================
    * Manages unique costcenter name and code for each company.
    """,
    'website': 'www.bistasolutions.com',
    'depends': ['analytic','account'],
    'data': [
        'security/analytic_extend_security.xml',
        'security/ir.model.access.csv',
        'views/analytic_account_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto-install':False,

}