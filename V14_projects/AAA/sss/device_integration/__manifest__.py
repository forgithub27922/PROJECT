# -*- encoding: utf-8 -*-
##############################################################################
#
#    Skyscend Business Solutions
#    Copyright (C) 2019 (http://www.skyscendbs.com)
#    Skyscend Business Solutions Pvt. Ltd.
#    Copyright (C) 2020 (http://wee.skyscendbs.com)
#
##############################################################################
{
    'name': 'Machine File Processing',
    'version': '14.0.0.1',
    'category': 'Others',
    'license': 'AGPL-3',
    'description': """
    This module is used to process the files and 
    communicate with panacim process tracker
    """,
    'author': 'Skyscend Business Solutions Pvt. Ltd.',
    'website': 'http://www.skyscendbs.com',
    'depends': ['base', 'base_setup', 'barcodes'],
    'data': [
        'security/machine_security.xml',
        'security/ir.models.access.csv',
        'views/res_config_settings_view.xml',
        'wizard/change_program_name_wiz_view.xml',
        'views/machine_view.xml',
        'wizard/scan_plc_wiz_view.xml',

    ],
    'installable': True,
    'auto_install': False
}
