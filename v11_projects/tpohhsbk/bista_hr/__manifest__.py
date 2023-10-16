# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Bista HR',
    'version': '11.0.0.1',
    'category': 'HR',
    'description': """
Bista HR
===========
    * Manage employee details.
    """,
    'author': 'Bista Solutions Pvt. Ltd.',
    'website': 'http://www.bistasolutions.com',
    'depends': ['base', 'hr', 'hr_contract', 'product', 'account_asset',
                'hr_recruitment', 'base_address_city'],
    'data': [
        # "security/hr_security.xml",
        # "security/ir.model.access.csv",
        # "data/ir_sequence_data.xml",
        # "data/employee_master_data.xml",
        # "data/employee_email_template.xml",
        # "data/res_request_link_data.xml",
        # "data/ir_sequence_scheduler.xml",
        # "views/hr_master_view.xml",
        # "views/employee_asset_view.xml",
        # 'views/res_config.xml',
        # 'views/res_bank_view.xml',
        # 'views/employee_salary_account_view.xml',
    ],
    'installable': True,
    'auto-install': True
}
