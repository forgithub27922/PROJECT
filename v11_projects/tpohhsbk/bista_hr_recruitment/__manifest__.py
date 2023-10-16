# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Employee Recruitment',
    'version': '11.0.1.0.0',
    'license': 'AGPL-3',
    'category': 'Generic Modules/Human Resources',
    'author': 'Bista Solutions Pvt. Ltd.',
    'website': 'http://bistasolutions.com',
    'depends': ['hr', 'hr_recruitment', 'hr_document', 'hr_payroll'],
    'data': [
        'security/hr_recruitment_security.xml',
        'security/ir.model.access.csv',
        'data/email_template.xml',
        'views/hr_recruitment.xml',
        'report/hr_interview_report.xml',
        'report/interview_report_view.xml',
        'views/job_offer_view.xml',
        'views/job_offer_report_tmpl.xml',
        'views/job_offer_report.xml',
        'wizard/job_offer_cancel.xml',
        'views/hr_salary_offer_details_view.xml',
        'data/hr_recruitment_stages_data.xml',
    ],
    'installable': True,
}
