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

# from ..unit.product_import import prepare_nonconfig_product_prices_batch_import
import logging
from datetime import datetime, timedelta

from odoo import models, fields, api
from odoo.exceptions import Warning

_logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-

from odoo import models, api

class ShopwareProductUpdateQueue(models.Model):
    _name = 'shopware6.product.update.queue'
    _description = 'Shopware6 product update queue'
    _order = 'write_date desc, id'

    product_id = fields.Many2one(comodel_name='product.product', required=True, index=True, ondelete='cascade')
    is_done = fields.Boolean("Is Done?", default=False)
    shopware6_bind_ids = fields.One2many(
        comodel_name='shopware6.price.queue',
        inverse_name='openerp_id',
        string='Shopware Price Queue Bindings',
    )

    def export_to_shopware(self):
        self.ensure_one()
        is_shopware = self.env['shopware6.product.product'].search([('openerp_id', '=', self.product_id.id)], limit=1, )
        if is_shopware:
            backends = self.env['shopware6.backend'].search([])
            for backend in backends:
                queue_binding = backend.create_bindings_for_model(self, 'shopware6_bind_ids')
        return True

class ProductMassUpdateQueue(models.Model):
    _name = 'product.mass.update.queue'
    _description = 'Product mass update queue'
    _order = 'write_date desc, id'

    product_id = fields.Many2one(comodel_name='product.product', required=True, index=True, ondelete='cascade')
    is_done = fields.Boolean("Is Done?", default=False)
    updated_fields = fields.Char("Updated Fields", default=[])
