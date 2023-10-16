# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010, 2014 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'GRIMM Tools',
    'version': '0.1',
    'application': False,
    'author': 'Dipak Suthar',
    'website': 'https://grimm-gastrobedarf.de',
    #~ 'license': 'LGPL-3',
    'category': 'Reporting',
    'summary': 'Grimm Tools',
    'description': """
        Main purpose of this module is to add all miscellaneous functionality created for colleagues which help to  improve their process like searching product in offer by supplier code etc.
    """,
    'depends': [
        'base',
        'sale',
        #'grimm_reports',
        'grimm_shopware6_connector',
        'fetchmail',
        #'web_notify',
        'purchase',
        'grimm_magentoerpconnect',
        'mass_operation_abstract'
    ],
    'data': [
        'views/receipt_label_report_view.xml',
        'views/general_view.xml',
        'views/grimm_tools_assets.xml',
        'views/email_template_view.xml',
        'views/label_printer_view.xml',
        'wizard/sale_order_cancel_reason_views.xml',
        'views/product_view.xml',
        'views/product_postalcode_view.xml',
        'security/ir.model.access.csv',
        'views/top_product_report_view.xml',
    ],
    'installable': True,
    'qweb': ['static/src/xml/mail_attachment.xml', ],
}
