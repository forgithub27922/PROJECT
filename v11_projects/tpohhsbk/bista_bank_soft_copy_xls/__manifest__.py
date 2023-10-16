# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Bank Soft Copy xls Report',
    'version': '11.0.0.1',
    'category': 'hr',
    'description': """
        Bank Soft Copy
    """,
    'author': 'Bista Solutions Pvt. Ltd.',
    'website': 'http://www.bistasolutions.com',
    'depends': ['hr', 'hr_payroll', 'bista_hr'],
    'external_dependencies': {'python': ['xlwt']},
    'data': [
        'security/ir_access_data.xml',
        'views/res_config_view.xml',
        'views/hr_payslip_view.xml',
        'views/hr_salary_rule.xml',
        'wizard/bank_soft_copy_xls_view.xml',
	    'wizard/payslip_report_view.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto-install': True,
}
