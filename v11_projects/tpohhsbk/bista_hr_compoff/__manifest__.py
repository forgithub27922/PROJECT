# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Bista HR Comp-Off',
    'version': '1.3',
    'category': 'Human Resources',
    'summary': 'Allow to request for comp-off.',
    'description': """
Bista HR Comp-Off
====================
* Allow to create/request, approve & given comp-off days.

* Configuration:
* Allow atleast one leave type of Comp-Off.
* Expired After: Comp-off days expired.
* Before Hours: Take an advance leave.
* Not allow to create leave request more than expire or max date end.
    """,
    'author': 'Bista Solutions Pvt. Ltd.',
    'website': 'http://www.bistasolutions.com',
    'depends': ['hr_holiday_extended', 'hr_timesheet'],
    'data': [
        'security/bista_hr_compoff_security.xml',
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'wizard/hr_compoff_given_view.xml',
        'views/hr_holidays_view.xml',
        'views/hr_compoff_view.xml',
    ],
    'installable': True,
}
