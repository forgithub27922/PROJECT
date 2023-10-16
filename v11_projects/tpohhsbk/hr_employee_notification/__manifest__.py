# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

{
    'name': 'Employee Notification',
    'version': '1.0',
    'author': 'Bista Solutions Pvt. Ltd.',
    'website': 'http://www.bistasolutions.com',
    'category': 'HR/Notifications',
    'depends': [
        'bista_hr'
    ],
    'data': [
        # 'data/templates.xml',
        'views/res_config_setting_view.xml',
        'data/alert_cron_jobs.xml',
        'data/email_template_for_expiry_date.xml',
    ],
    'demo': [],
    'insallable': True,
    'auto_install': False,
    'application': True
}
