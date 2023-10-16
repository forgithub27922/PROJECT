# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#
##############################################################################
{
    'name': 'Recruitment Custom',
    'version': '13.0.0.1',
    'category': 'HR',
    'description': """
    This module is used add fields and process on recruitment
    """,
    'author': 'Skyscend Business Solutions',
    'website': 'http://www.skyscendbs.com',
    'depends': ['sky_hr_custom', 'hr_recruitment', 'base_address_city', 'contacts'],
    'data': [
        'data/res.city.csv',
        'data/sky_mail_template.xml',
        'security/ir.model.access.csv',
        'views/hr_recruitment_view.xml',
        'views/cancel_applicant_wizard_view.xml',
        'views/hr_interview_view.xml',
        'views/reject_applicant_wizard_view.xml',
        'views/update_schedule_interview_wizard_view.xml',
        'views/print_report_wizard_view.xml',
        'data/accept_applicant_email_template_view.xml',
        'data/cancel_applicant_email_template_view.xml',
        'data/reject_applicant_email_template_view.xml',
        'data/schedule_interview_email_template_view.xml',
        'report/hr_applicant_report.xml',
        'report/hr_applicant_template_view.xml',
        'views/pending_document_wizard_view.xml',
        'data/pending_document_email_template_view.xml',
    ],
    'installable': True,
    'auto_install': False
}
