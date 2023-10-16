# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'HR Document',
    'version': '11.0.1.0.0',
    'license': 'AGPL-3',
    'category': 'Generic Modules/Human Resources',
    'author': 'Bista Solutions Pvt. Ltd.',
    'website': 'http://bistasolutions.com',
    'depends': ['hr_contract', 'hr_recruitment', 'bista_hr'],
    'external_dependencies': {'python': ['bs4']},
    'data': [
        'data/hr_data.xml',
        'security/ir.model.access.csv',
        'security/hr_document_security.xml',
        'views/hr_document_view.xml',
        'report/hr_document_report.xml',
        'report/report_view.xml',
        'wizard/employee_docs.xml',

    ],
    'installable': True,
}
