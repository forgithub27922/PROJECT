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


from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping


class ProductAttributeSetBatchImport(Component):
    _name = 'magento.product.attribute.set.batch.importer'
    _inherit = 'magento.delayed.batch.importer'
    _apply_on = ['magento.product.attribute.set']


class ProductAttributeSetImport(Component):
    _name = 'magento.product.attribute.set.importer'
    _inherit = 'magento.importer'
    _apply_on = ['magento.product.attribute.set']


class ProductAttributeSetImportMapper(Component):
    _name = 'magento.product.attribute.set.import.mapper'
    _inherit = 'magento.import.mapper'
    _apply_on = ['magento.product.attribute.set']

    direct = [
        ('name', 'name'),
        ('set_id', 'magento_id')
    ]

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}
