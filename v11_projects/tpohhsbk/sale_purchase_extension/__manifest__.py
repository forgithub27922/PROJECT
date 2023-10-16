# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2018 (http://www.bistasolutions.com)
#
##############################################################################
{
    'name': 'Bista Sale Purchase Extension',
    'description': """
        This Module Customized Sale Purchase Extension.
    """,
    'version': '1.0',
    'category': 'general',
    'website': 'www.bistasolutions.com',
    'author': 'Bista Solutions Pvt. Ltd.',
    'maintainer': 'Bista Solutions Pvt. Ltd.',
    'depends': ['base', 'sale_stock','purchase'],
    'data': [
            'security/security.xml',
            'views/account_invoice_view.xml',
            'views/sale_order_view.xml',
            'views/res_users.xml',
    ],
    'auto_install': False,
    'application': False,
    'installable': True
}
