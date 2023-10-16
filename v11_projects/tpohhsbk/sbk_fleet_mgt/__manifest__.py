# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'SBK Fleet Management',
    'version': '1.0',
    'category': 'Fleet',
    'description': """
        This Module Provide the Fleet Management Feature.
    """,
    'author': 'Bista Solutions Pvt. Ltd.',
    'website': 'http://www.bistasolutions.com',
    'depends': ['fleet','bista_hr','board'],
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/fleet_vehicle_view.xml',
        'views/fleet_vehicle_registration_view.xml',
        'views/fleet_vehicle_insurance_view.xml',
        'views/res_partner_view.xml',
        'views/res_company_view.xml',
        'views/emp_document_dashboard_view.xml'
    ],
    'auto_install': False,
    'application': False,
    'installable': True
}
