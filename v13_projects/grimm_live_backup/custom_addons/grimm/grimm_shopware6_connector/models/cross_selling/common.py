# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import xmlrpc.client

from collections import defaultdict

from odoo import models, fields, api
from odoo.addons.connector.exception import IDMissingInBackend
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.queue_job.job import job, related_action
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class SparePartProduct(models.Model):
    _inherit = 'spare.part.product'

    sequence = fields.Integer('Position', default=0)

class AccessoryPartProduct(models.Model):
    _inherit = 'accessory.part.product'

    _order = 'sequence, id'

    sequence = fields.Integer('Position', default=0)
    product_id = fields.Many2one('product.product', string='Related Product', ondelete='cascade')
    rel_sequence = fields.Integer('Position', related="sequence", store=True, readonly=False)

    shopware6_bind_ids = fields.One2many(
        comodel_name='shopware6.accessory.part.product',
        inverse_name='openerp_id',
        string="Shopware6 Bindings",
    )
    image_1920 = fields.Image("Image",related='accessory_part_id.image_1920')
    accessory_active = fields.Boolean("Accessory Active", related='accessory_part_id.active')
    accessory_shopware_active = fields.Boolean("Accessory Shopware Active", related='accessory_part_id.shopware_active')
    is_shopware_exported = fields.Boolean(string='Is Exported ?', compute='_get_is_shopware_exported')
    def _get_is_shopware_exported(self):
        for this in self:
            this.is_shopware_exported = False
            for bind in this.shopware6_bind_ids:
                if bind.shopware6_id:
                    this.is_shopware_exported = True
                    pass

class Shopware6AccessoryPartProdut(models.Model):
    _name = 'shopware6.accessory.part.product'
    _inherit = 'shopware6.binding'
    _inherits = {'accessory.part.product': 'openerp_id'}
    _description = 'Shopware6 Accessory Part Product'


    openerp_id = fields.Many2one(comodel_name='accessory.part.product',
                                 string='Accessory Part Product',
                                 required=True, ondelete='cascade')


class AccessoryPartProductAdapter(Component):
    _name = 'shopware6.accessory.part.product.adapter'
    _inherit = 'shopware6.adapter'
    _apply_on = ['shopware6.accessory.part.product']

    _shopware_uri = 'api/v3/product-cross-selling-assigned-products/'

class Shopware6AccessoryPartProduct(Component):
    _name = 'shopware6.accessory.part.product.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['shopware6.accessory.part.product']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        record.with_delay().export_record()

class AccessoryPartProductListener(Component):
    _name = 'accessory.part.product.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['accessory.part.product']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        for shopware_bind in record.shopware6_bind_ids:
            if record.product_id:
                shopware_bind.with_delay(description="Export Accessory parts for %s product"%record.product_id.default_code or "").export_record(fields=fields)

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_unlink(self, record):
        for binding in record.shopware6_bind_ids:
            target_shopware_id = getattr(binding, 'shopware6_id')
            if target_shopware_id:
                binding.with_delay().export_delete_record(binding.backend_id, target_shopware_id)