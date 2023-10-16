# -*- encoding: utf-8 -*-
##############################################################################
#
#    Skyscend Business Solutions
#    Copyright (C) 2016 (http://www.skyscendbs.com)
#
##############################################################################
{
    'name': 'Fleet Transactions',
    'version': '1.0',
    'author': 'Skyscend Business Solutions',
    'sequence': 1,
    'category': 'tools',
    'website': 'http://www.skyscendbs.com',
    'summary': 'Fleets Transactions such as Transfer, Sell, Scrap Gift etc.',
    'description': """
    This module is used to have the transactions for the fleet.
    """,
    'depends': [
        'fleet', 'sbk_fleet_mgt'
    ],
    'data': [
        'security/fleet_security.xml',
        'security/ir.model.access.csv',
        'data/fleet_transaction_sequence.xml',
        'views/fleet_view.xml',
        'report/fleet_transaction_report.xml',
        'views/vehicle_report_by_driver_view.xml',
        'views/vehicle_report_by_driver_template.xml',
        'views/vehicle_report_by_location_view.xml',
        'views/vehicle_report_by_location_template.xml',
        'views/vehicle_report_by_vehicle_view.xml',
        'views/vehicle_report_by_vehicle_template.xml',
        'views/vehicle_report_by_period_view.xml',
        'views/vehicle_report_by_period_template.xml',
    ],

    'installable': True,
    'auto_install':False
}