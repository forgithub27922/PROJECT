{
    'name': 'Sky Account Transactions',
    'version': '13.0.0.1',
    'category': 'Account',
    'description': """
    This module is for account transactions""",
    'author': 'Skyscend Business Solutions',
    'website': 'http://www.skyscendbs.com',
    'depends': ['account', 'base', 'base_accounting_kit', 'sky_hr_custom'],
    'data': [
        'security/ir.model.access.csv',
        'data/transaction_sequence.xml',
        'views/account_transactions.xml',
    ],
    'installable': True,
    'auto_install': False
}
