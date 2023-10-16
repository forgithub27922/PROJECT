# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Bista PDC Management',
    'version': '11.0.1.0',
    'author': 'Bista Solutions',
    'website': 'http://www.bistasolutions.com',
    'category': 'Accounting',
    'summary': 'Extension on Cheques to handle Post Dated Cheques',
    'description': """ Extension on Cheques to handle Post Dated Cheques """,
    'depends': ['account', 'account_check_printing', 'account_cancel'],
    'data': [
        'data/pdc_scheduler.xml',
        'data/account_pdc_data.xml',
        'views/account_payment_view.xml',
        'views/res_config_view.xml',
        'views/sale_order_line.xml',
        'wizard/pdc_payment_wiz_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
