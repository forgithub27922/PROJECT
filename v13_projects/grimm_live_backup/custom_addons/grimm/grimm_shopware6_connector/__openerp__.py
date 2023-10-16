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
    'name': 'Grimm Shopware6 Connector',
    'version': '0.1',
    'application': False,
    'author': 'Dipak Suthar',
    'website': 'https://grimm-gastrobedarf.de',
    'category': 'connector',
    'summary': 'Enhancement of based Shopware6 Connector for Grimm.',
    'description': """
        This module is enhancement of based Shopware6 connector specially for Grimm.
    """,
    'depends': ['shopware6_connector', 'of_base_magento_extensions_v9'],
    'data': [
        'data/connector_shopware_data.xml',
        'security/ir.model.access.csv',
        'views/models/template.xml',
        'views/menu.xml',
        'views/models/option.xml',
        'views/models/option_value.xml',
        'views/product_template.xml',
        'views/product_product.xml',
        'views/product_advance_filter_view.xml',
        'views/product_image.xml',
        'views/delivery_time_view.xml',
        'views/media_manager_view.xml',
        'views/backend_view.xml',
        'views/sale_order_view.xml',
        'views/product_category_view.xml',
    ],
    'installable': True,
}
