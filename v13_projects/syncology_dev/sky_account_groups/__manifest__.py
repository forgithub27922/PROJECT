{
    'name': 'Sky Account Groups',
    'version': '13.0.0.1',
    'category': 'Account',
    'description': """
    This module is for account groups""",
    'author': 'Skyscend Business Solutions',
    'website': 'http://www.skyscendbs.com',
    'depends': ['base', 'base_accounting_kit', 'sky_hr_custom', 'account'],
    'data': [
        'data/journal_sequence.xml',
        'views/account_move.xml',
        'views/account_views.xml',
        'views/account_payment.xml'
    ],
    'installable': True,
    'auto_install': False
}
