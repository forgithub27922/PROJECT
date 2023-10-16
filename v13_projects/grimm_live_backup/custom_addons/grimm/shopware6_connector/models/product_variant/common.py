# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


import xmlrpc.client
import uuid
import json
from datetime import datetime

from collections import defaultdict

from odoo import api, fields, models, tools, _
from odoo.addons.connector.exception import IDMissingInBackend
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.queue_job.job import job, related_action
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)


class Shopware6ProductProduct(models.Model):
    _name = 'shopware6.product.product'
    _inherit = 'shopware6.binding'
    _inherits = {'product.product': 'openerp_id'}
    _description = 'Shopware6 Product'

    @api.model
    def product_type_get(self):
        return [
            ('simple', 'Simple Product'),
            ('configurable', 'Configurable Product'),
            ('virtual', 'Virtual Product'),
            ('downloadable', 'Downloadable Product'),
            ('giftcard', 'Giftcard')
            # XXX activate when supported
            # ('grouped', 'Grouped Product'),
            # ('bundle', 'Bundle Product'),
        ]

    ptmpl_openerp_id = fields.Many2one(
        'product.template',
        related='openerp_id.product_tmpl_id',
        string='Openerp ptmpl ID',
        store=True
    )
    openerp_id = fields.Many2one(comodel_name='product.product',
                                 string='Product',
                                 required=True,
                                 ondelete='cascade')
    shopware6_qty = fields.Float(string='Computed Quantity',
                               help="Last computed quantity to send "
                                    "on Shopware6.")
    no_stock_sync = fields.Boolean(
        string='No Stock Synchronization',
        required=False,
        help="Check this to exclude the product "
             "from stock synchronizations.",
    )


class ProductProduct(models.Model):
    _inherit = 'product.product'

    shopware6_bind_ids = fields.One2many(
        comodel_name='shopware6.product.product',
        inverse_name='openerp_id',
        string='Shopware6 Bindings',
    )
    sales_channel_ids = fields.Many2many(comodel_name='sales.channel', relation='product_product_sales_channel_rel')
    shopware6_category_ids = fields.Many2many(comodel_name='product.category',string='Shopware Categories', copy=True)

    product_media_ids = fields.One2many(
        comodel_name='product.media',
        inverse_name='product_id',
        string='Product Media',
    )
    shopware6_version_id = fields.Char(string='Shopware6 Version')

class Shopware6BindingProductProductListener(Component):
    _name = 'shopware6.binding.product.product.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['shopware6.product.product']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        if record._context.get("export_now", False):
            record.export_record()
        else:
            record.with_delay().export_record()
class Shopware6ProductProductListener(Component):
    _name = 'shopware6.product.product.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['product.product']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        if "delete_shopware_product" in fields:
            for binding in record.shopware6_bind_ids:
                target_shopware_id = getattr(binding, 'shopware6_id')
                if target_shopware_id:
                    try:
                        binding.export_delete_record(binding.backend_id, target_shopware_id)
                    except:
                        pass
                    binding.unlink()
            return True

        if not record.active:
            self.env.cr.execute("select id from shopware6_product_product where openerp_id=%s limit 1" % (record.id))
            product_ids = [x[0] for x in self.env.cr.fetchall()]
            if product_ids:
                bind_id = self.env["shopware6.product.product"].browse(product_ids)
                with bind_id.backend_id.work_on("shopware6.product.product") as work:
                    product_adapter = work.component(usage='backend.adapter', model_name='shopware6.product.product')
                    try:
                        _logger.info("Odoo going to deactivate product on shopware %s "%bind_id.shopware6_id)
                        product_adapter.write(bind_id.shopware6_id, {'active':False})
                    except:
                        pass

        for pp_bind in record.shopware6_bind_ids:
            direct_fields = ['meta_description', 'package_id', 'description_sale', 'warranty_type', 'width', 'ean_number', 'manufacture_code', 'weight', 'grimm_product_custom_product_template_id', 'default_code', 'height', 'length', 'used_in_manufacturer_listing', 'short_description', 'shopware6_category_ids', 'is_spare_part', 'taxes_id', 'meta_title', 'supplier_taxes_id', 'search_words', 'shopware6_delivery_time_id', 'name', 'attribute_line_ids', 'is_package', 'product_brand_id', 'description', 'rrp_price', 'shopware_active', 'warranty', 'company_id']
            if all(field in direct_fields for field in fields):

                existing_record = self.env['product.mass.update.queue'].search([('product_id', '=', record.id), ('is_done', '=', False)])
                if existing_record:
                    field_list = json.loads(existing_record.updated_fields)
                    field_list.extend(fields)
                    existing_record.updated_fields = json.dumps(list(set(field_list)))
                else:
                    self.env['product.mass.update.queue'].create({'product_id': record.id, 'updated_fields': json.dumps(fields)})
            else:
                pp_bind.with_delay(description="Export %s product to Shopware"%record.default_code or "").export_record(fields=fields)