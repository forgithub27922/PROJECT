# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'End of Service',
    'version': '1.2',
    'category': 'Human Resources',
    'summary': 'Manage End of Service of employee',
    'description': """
Manage End of Service of employee
=================================

This application handle employee end of service process
    """,
    'author': 'Bista Solutions Pvt. Ltd.',
    'website': 'https://www.bistasolutions.com/',
    'depends': ['account_asset', 'hr_document'],
    'external_dependencies': {'python': ['bs4']},
    'data': [
        'security/hr_termination_security.xml',
        'security/ir.model.access.csv',
        'data/termination_request_mail_template.xml',
        'views/hr_view.xml',
        'views/hr_termination_request_view.xml',
        'wizard/wiz_reject_request_view.xml',
        'views/hr_document_view.xml',
        'views/hr_document_report.xml',
        'views/report_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
