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
    'name': 'Shopware6 Connector',
    'version': '0.1',
    'application': False,
    'author': 'Dipak Suthar',
    'website': 'https://grimm-gastrobedarf.de',
    #~ 'license': 'LGPL-3',
    'category': 'connector',
    'summary': 'Shopware 6 Connector',
    'description': """
        Odoo-Shopware connector.
    """,
    'depends': ['base', 'sale', 'connector', 'stock', 'sale_management', 'grimm_magentoerpconnect'],
    'data': [
        'data/connector_shopware_data.xml',
        'views/backend_view.xml',
        'views/media_folder_view.xml',
        'views/product_media_view.xml',
        'views/sales_channel_view.xml',
        'views/product_view.xml',
        'views/product_category_view.xml',
        'views/res_partner_view.xml',
        'views/product_attribute_view.xml',
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
    ],
    'installable': True,
}
