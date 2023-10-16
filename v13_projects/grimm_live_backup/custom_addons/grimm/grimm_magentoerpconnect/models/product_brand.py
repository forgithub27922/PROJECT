# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2017 Openfellas (http://openfellas.com) All Rights Reserved.
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

from odoo import models, fields, api


class GrimmProductBrand(models.Model):
    _inherit = 'grimm.product.brand'

    magento_value_map_ids = fields.One2many('product.brand.magento.mapping', 'brand_id',
                                            string='Magento brand mappings')

    def get_magento_brand_value(self, backend_id):
        self.ensure_one()
        res = None

        for line in self.magento_value_map_ids.filtered(lambda rec: rec.backend_id.id == backend_id):
            res = line.brand_magento_attr_value_id

        return res


class ProductBrandMagentoMapping(models.Model):
    _name = 'product.brand.magento.mapping'
    _description = 'Product brand magento mapping'

    backend_id = fields.Many2one('magento.backend', string='Magento backend')
    brand_id = fields.Many2one('grimm.product.brand', string='Grimm product brand')
    brand_magento_attr_value_id = fields.Many2one('magento.product.attribute.value', string='Magento attribute value')

    _sql_constraints = [
        ('backend_id_uniq', 'unique(backend_id, brand_id)',
         'You can not assign more than one attribute value per Magento backend!'),
    ]
