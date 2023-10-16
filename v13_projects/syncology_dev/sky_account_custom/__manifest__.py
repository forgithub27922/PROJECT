# -*- encoding: utf-8 -*-
#######################################################################################
#
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#    Copyright (C) 2020 Skyscend Business Solutions  Pvt. Ltd.(<http://skyscendbs.com>)
#
#######################################################################################
{
    'name': 'Sky Account Custom',
    'version': '13.0.0.1',
    'description': "This module is used for adding opening balance in balance sheet report",
    'author': 'Skyscend Business Solutions Pvt. Ltd.',
    'website': 'http://www.skyscendbs.com',
    'depends': ['base_accounting_kit'],
    'data': [
        'report/report_financial_template.xml',
    ],
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}
