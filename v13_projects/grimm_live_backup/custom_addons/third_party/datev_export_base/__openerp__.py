# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2016 Openfellas (http://openfellas.com) All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly advised to contract support@openfellas.com
#
##############################################################################


{
    'name': 'Export to Datev - Base',
    'version': '1.0 (9.0)',
    'category': 'Accounting & Finance',
    'complexity': 'normal',
    'description': """
     This module provides base settings for DATEV export moudules

     Format: DATEV XML Interface Online 3.0

     DATEV is the leading accounting software in germany used by many
     tax advisors.
    
    """,
    'author': 'openfellas',
    'depends': ['base', 'account'],
    "data": [
        'company_view.xml',
        'res_partner_view.xml',
        'account/views/account_view.xml',
    ],
    'demo_xml': [],
    'installable': True,
}