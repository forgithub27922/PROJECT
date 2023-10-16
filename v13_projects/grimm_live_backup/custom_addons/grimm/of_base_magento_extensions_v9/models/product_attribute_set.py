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

from odoo import models, fields, api
from odoo.addons.queue_job.job import job, related_action
from odoo.tools.translate import _

from ..constants import ATTRS_ODOO_MASTER


class ProductAttributeSet(models.Model):
    _inherit = 'product.attribute.set'

    magento_binding_ids = fields.One2many('magento.product.attribute.set', 'openerp_id', string='Magento bindings')
    skeleton_attribute_set_id = fields.Many2one('product.attribute.set', string='Based on')
    should_export = fields.Boolean(string='Export condition', compute='_compute_should_export')

    def _compute_should_export(self):
        backends = self.env['magento.backend'].search([]).filtered(
            lambda rec: rec.product_attributes_sync_type == ATTRS_ODOO_MASTER)
        for attr_set in self:
            attr_set.should_export = len(backends) > 0

    def write(self, vals):
        res = True

        if 'product_attribute_ids' in vals:
            for rec in self:
                rec = rec.with_context(attribute_ids_before_update=rec.product_attribute_ids.ids)
                res = res and super(ProductAttributeSet, rec).write(vals)
        else:
            res = super(ProductAttributeSet, self).write(vals)

        return res

    def button_export_to_magento(self):
        self.ensure_one()
        if not self.skeleton_attribute_set_id:
            raise Warning(_('First you must provide base attribute set with Magento binding!'))

        return self.create_bindings()

    def _prepare_specific_binding_vals(self, backend):
        self.ensure_one()
        return {
            'magento_id': None
        }

    def create_bindings(self):
        self.ensure_one()
        backends = self.env['magento.backend'].search([('product_attributes_sync_type', '=', ATTRS_ODOO_MASTER)])
        for backend in backends:
            backend.create_bindings_for_model(self, 'magento_binding_ids')


class MagentoProductAttributeSet(models.Model):
    _name = 'magento.product.attribute.set'
    _description = 'Magento product attribute'
    _inherit = 'magento.binding'
    _inherits = {'product.attribute.set': 'openerp_id'}

    openerp_id = fields.Many2one('product.attribute.set', 'Product attribute set', required=True, ondelete='cascade')
    magento_attribute_ids = fields.Many2many(
        comodel_name='magento.product.attribute',
        compute='_compute_magento_attribute_ids',
        string='Magento attributes'
    )

    @api.depends('openerp_id.product_attribute_ids', 'openerp_id.product_attribute_ids.magento_binding_ids')
    def _compute_magento_attribute_ids(self):
        for record in self:
            res = []

            for attr in record.openerp_id.product_attribute_ids:
                for attr_bind in attr.magento_binding_ids:
                    if attr_bind.backend_id.id == record.backend_id.id:
                        res.append(attr_bind.id)

            record.magento_attribute_ids = res

    @api.model
    def fields_to_update_on_magento(self):
        return ['product_attribute_ids']

    _sql_constraints = [
        ('backend_oe_uniq', 'unique(backend_id, openerp_id)',
         'Odoo product attribute set can be linked with only one product attribute set per Magento backend!'),
    ]

    @job(default_channel='root.magento')
    def adjust_attribute_on_attrset(self, attribute_id, attribute_set_id, action):
        """ Export the inventory configuration and quantity of a product. """
        self.ensure_one()
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.adjust_attribute_on_set(attribute_id, attribute_set_id, action)
