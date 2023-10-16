# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2018 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Account Report',
    'description': """
     
    """,
    'version': '1.0',
    'category': 'Account',
    'website': 'www.bistasolutions.com',
    'author': 'Bista Solutions Pvt. Ltd.',
    'maintainer': 'Bista Solutions Pvt. Ltd.',
    'depends': ['base', 'account_accountant', 'analytic', 'bista_analytic_account'],
    'data': [
        # 'data/base_data.xml',
        'report/account_report_temp.xml',
        'views/account_report.xml',
        'views/account_journal_view.xml',
        'views/payment_receipt_report.xml',
        'wizard/account_report_wiz_view.xml',
        'wizard/analytic_account_report_wiz_view.xml',
        'report/analytic_account_report_temp.xml',
        'wizard/balance_sheet_acc_grp_view.xml',
        'report/balance_sheet_account_grp_report.xml',
        'wizard/account_trial_bal_wiz.xml',
        'report/account_trial_bal_report_tmpl.xml',
        'wizard/wizard_consolidate_report_view.xml',
        'wizard/wizard_bs_consolidate_report_view.xml',
        'wizard/wizard_consolidate_trial_balance_report.xml',
        'wizard/wizard_pnl_consolidate_report_view.xml',
    ],
    'demo': [],
    'auto_install': False,
    'application': False,
    'installable': True
}
