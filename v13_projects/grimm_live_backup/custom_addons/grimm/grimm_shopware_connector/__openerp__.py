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
    'name': 'Grimm Shopware Connector',
    'version': '0.1',
    'application': False,
    'author': 'Dipak Suthar',
    'website': 'https://grimm-gastrobedarf.de',
    'category': 'connector',
    'summary': 'Enhancement of based Shopware Connector for Grimm.',
    'description': """
        This module is enhancement of based Shopware connector specially for Grimm.
    """,
    'depends': ['shopware_connector', 'asset_base', 'of_base_magento_extensions_v9'],
    'data': [
        'views/product_view.xml',
        'security/ir.model.access.csv',
        'views/shopware_backend_view.xml',
        'views/data.xml',
    ],
    'installable': True,
}
