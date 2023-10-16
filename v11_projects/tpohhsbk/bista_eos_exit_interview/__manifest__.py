# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'EOS - Exit Interview & Survey',
    'version': '1.1',
    'category': 'Human Resources',
    'summary': 'Manage End of Service & Exit Interview Survay',
    'description': """
EOS - Exit Interview & Survey
=================================
    * Allow to manage exit interview survay.
    """,
    'author': 'Bista Solutions Pvt. Ltd.',
    'website': 'https://www.bistasolutions.com/',
    'depends': ['bista_eos', 'survey'],
    'data': [
        'security/ir.model.access.csv',
        'security/hr_termination_security.xml',
        'views/hr_termination_request_view.xml',
        'views/exit_interview_view.xml',
        'views/survey_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
