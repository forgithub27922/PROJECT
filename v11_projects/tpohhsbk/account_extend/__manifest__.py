{
    'name': 'Account Extend',
    'version': '1.0',
    'author': 'Bista Solutions',
    'sequence': 10,
    'category': 'Accounting',
    'description': """
Account Extend
=================
    * Invoice report should be Tax Invoice.
    """,
    'website': 'www.bistasolutions.com',
    'depends': ['account'],
    'data': [
        'views/account_view.xml',
        'views/invoice_report.xml',
        'views/account_payment_views.xml',
        'reports/journal_audit_report.xml',
        'reports/report.xml',
        'reports/account_move_report_template.xml',
        'views/account_move_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto-install':False,

}