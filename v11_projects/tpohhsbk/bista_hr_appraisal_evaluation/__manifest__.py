# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Appraisal Evaluation',
    'description': """
    - Employee Performance Appraisal Evaluation
    """,
    'version': '1.0',
    'category': 'hr',
    'website': 'www.bistasolutions.com',
    'author': 'Bista Solutions Pvt. Ltd.',
    'maintainer': 'Bista Solutions Pvt. Ltd.',
    'depends': [
        'base', 'hr', 'hr_recruitment'
    ],
    'data': [
        'security/user_groups.xml',
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'wizard/hr_kra_approve_all_wiz.xml',
        'wizard/annual_evaluation_report_wiz.xml',
        'views/hr_appraisal_configuration_view.xml',
        'views/hr_kra_configuration_view.xml',
        'views/hr_employee_kra.xml',
        'wizard/hr_kra_generate_wiz.xml',
        'views/email_templates.xml',
        'report/appraisal_kra_report.xml',
        'report/annual_appraisal_report.xml',
        'report/report_registration.xml',
        'views/menu_items_view.xml',
    ],
    'demo': [],
    'auto_install': False,
    'application': True,
    'installable': True
}
