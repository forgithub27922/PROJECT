##########################################################################################
#
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#    Copyright (C) 2020 Skyscend Business Solutions Pvt. Ltd. (http://www.skyscendbs.com)
#
##########################################################################################
{
    'name': 'Merge Invoice Order',
    'description': 'This module merge the invoice orders',
    'version': '1.0',
    'author': 'Skyscend Business Solution Pvt. Ltd.',
    'website': 'www.skyscendbs.com',
    'depends': [
        'account'
    ],
    'data': [
        'security/merge_invoices_order_security.xml',
        'security/ir.model.access.csv',
        'wizard/merge_invoice_order.xml',
    ],
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3'
}
