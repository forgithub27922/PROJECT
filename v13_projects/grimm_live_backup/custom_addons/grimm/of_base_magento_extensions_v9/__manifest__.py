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
##############################################################################

{'name': 'Openfellas Magento Connector Extensions',
 'version': '1.0',
 'category': 'Connector',
 'depends': ['connector_magento', 'grimm_product', 'asset_base', 'grimm_pretext_template'],
 'external_dependencies': {
     'python': ['magento'],
 },
 'author': "Openfellas",
 'license': 'AGPL-3',
 'website': 'http://www.openfellas.com',
 'images': [],
 'demo': [],
 'data': [
     'views/magento_backend.xml',
     'views/product_attribute_set.xml',
     #'views/product_attribute.xml', # odoo13change
     #'views/product.xml',
     'views/product_image.xml',
     'security/ir.model.access.csv',
     'data.xml',
     'init_query.sql'
 ],
 'installable': True,
 'application': True,
 }
