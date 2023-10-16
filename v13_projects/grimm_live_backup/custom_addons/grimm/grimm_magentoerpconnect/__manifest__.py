# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2016 Openfellas (http://openfellas.com) All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly advised to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
###############################################################################

{'name': 'Grimm Magento Connector Extensions',
 'version': '1.0',
 'category': 'Connector',
 'depends': [
     'of_base_magento_extensions_v9',
     # 'grimm_extensions',
     # 'web_tree_image',
     'account',
     'product',
     # 'web_m2x_options',
     'asset_base',
     'grimm_pricelist',
     'grimm_product'
 ],
 'external_dependencies': {
     'python': ['magento'],
 },
 'author': "Openfellas",
 'license': 'AGPL-3',
 'website': 'http://www.openfellas.com',
 'images': [],
 'demo': [],
 'data': [
     'views/product.xml',
     'views/magento_backend.xml',
     'views/sale_view.xml',
     'views/account_view.xml',
     'views/product_image_view.xml',
     'data.xml',
     'security/ir.model.access.csv'
 ],
 'installable': True,
 'application': True,
 }
