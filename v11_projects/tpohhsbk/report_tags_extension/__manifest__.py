# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': "Report Account Extension",
    'version': "1.18",
    'category': "account",
    'sequence': 4,
    'summary': "Report filtering with Account Id",
    'description': """
Report Account Extension
=========================
    * Accounting Reports: Allow filter by accounts in the reports.
    """,
    'author': "Bista solutions Pvt Ltd",
    'website': "https://www.bistasolutions.com",
    'images': [],
    'depends': [
        'account',
        'account_reports',
    ],
    # data files always loaded at installation
    'data': [
        'views/report_template.xml',
    ],
    # data files containing optionally loaded demonstration data
    'demo': [
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
