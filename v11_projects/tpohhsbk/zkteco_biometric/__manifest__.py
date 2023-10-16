# -*- coding: utf-8 -*-
##############################################################################
#
# Skyscend Business Soluitions
# Copyright (C) 2019  (http://www.skyscendbs.com)
#
# Skyscend Business Soluitions Pvt. Ltd.
# Copyright (C) 2020  (http://www.skyscendbs.com)
##############################################################################
{
    'name' : 'Zkteco Biometric',
    'author':'Skyscend Business Solutions Pvt. Ltd.',
    'version' : '1.0',
    'summary': 'Biometric Attendance',
    'description':'Zkteco  and eSSL companies most of device supported',
    'category': 'biometric',
    'website': 'https://www.skyscendbs.com',
    'depends': ['hr_attendance'],
    'data': [
            'security/ir.model.access.csv',
            'views/bio_attendance.xml',
            'views/bio_config.xml',
            'views/guest_users.xml',
            'views/bio_cron.xml',
            'wizard/sh_message_wizard.xml'
            ],
    'installable': True,
}
