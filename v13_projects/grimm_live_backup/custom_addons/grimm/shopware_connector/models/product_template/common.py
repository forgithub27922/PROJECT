# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import xmlrpc.client
import uuid
from datetime import datetime

from collections import defaultdict

from odoo import api, fields, models, tools, _
from odoo.addons.connector.exception import IDMissingInBackend
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.queue_job.job import job, related_action
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class ShopwareProductProduct(models.Model):
    _name = 'shopware.product.template'
    _inherit = 'shopware.binding'
    _inherits = {'product.template': 'openerp_id'}
    _description = 'Shopware Product'


    created_at = fields.Datetime('Created At (on Shopware)')
    updated_at = fields.Datetime('Updated At (on Shopware)')
    last_job_status = fields.Char('Last Job Status', compute='_compute_last_job_state')

    openerp_id = fields.Many2one(comodel_name='product.template',
                                 string='Product',
                                 required=True,
                                 ondelete='cascade')
    # XXX website_ids can be computed from categories
    website_ids = fields.Many2many(comodel_name='shopware.shop',
                                   string='Shopware Shop',
                                   readonly=True)
    shopware_created_at = fields.Date('Created At (on Shopware)')
    shopware_updated_at = fields.Date('Updated At (on Shopware)')

    manage_shopware_stock = fields.Selection(
        selection=[('use_default', 'Use Default Config'),
                   ('no', 'Do Not Manage Stock'),
                   ('yes', 'Manage Stock')],
        string='Manage Stock Level',
        default='use_default',
        required=True,
    )
    shopware_backorders = fields.Selection(
        selection=[('use_default', 'Use Default Config'),
                   ('no', 'No Sell'),
                   ('yes', 'Sell Quantity < 0'),
                   ('yes-and-notification', 'Sell Quantity < 0 and '
                                            'Use Customer Notification')],
        string='Manage Inventory Backorders',
        default='use_default',
        required=True,
    )
    shopware_qty = fields.Float(string='Computed Quantity',
                               help="Last computed quantity to send "
                                    "on Shopware.")
    no_stock_sync = fields.Boolean(
        string='No Stock Synchronization',
        required=False,
        help="Check this to exclude the product "
             "from stock synchronizations.",
    )

    RECOMPUTE_QTY_STEP = 1000  # products at a time

    def _compute_last_job_state(self):
        for tmpl in self:
            queue_id = tmpl.sudo().queue_ids.sorted(key=lambda r: r.id, reverse=True)
            tmpl.last_job_status = 'pending'
            if queue_id:
                tmpl.last_job_status = queue_id[0].state

    @job(default_channel='root.shopware')
    @related_action(action='related_action_unwrap_binding')
    def export_record(self, fields=None):
        """ Export a Product to Shopware. """
        self.ensure_one()
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            return exporter.run(self, fields)

    @job(default_channel='root.shopware')
    @related_action(action='related_action_unwrap')
    def batch_export_record(self, ids=None, data = {},fields = None):
        """ Export a batch Product to Shopware. """
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            queue_vals = {
                'name': 'Batch Export Shopware Product',
                'company_id': self.backend_id.default_company_id.id,
                'user_id': 1,
                'state': 'failed',
                'date_created': str(datetime.now()),
                'date_started': str(datetime.now()),
                'model_name': 'shopware.product.template',
                'method_name': 'export_record',
                'uuid': str(uuid.uuid1()),
            }
            queue_id = self.env["queue.job"].create(queue_vals) # Due to batch export we need to create job queue explicitly for display purpose only.
            result = exporter.backend_adapter.write(False, data)
            if result.get("success", False) and queue_id:
                queue_id.date_done = str(datetime.now())
                queue_id.state = 'done'
                queue_id.result = "Product batch is exported with these IDS %s"%ids
            return result

    def batch_json_export_record(self, fields=None):
        """ Export a Product to Shopware. """
        self.ensure_one()
        with self.backend_id.work_on(self._name) as work:
            exporter = work.component(usage='record.exporter')
            print("Calling batch JSON export method")
            return exporter.create_batch_json(self, fields)

    @job(default_channel='root.shopware')
    @related_action(action='related_action_shopware_link')
    def export_delete_record(self, backend, shopware_id):
        """ Delete a Product record on Shopware """
        with backend.work_on(self._name) as work:
            deleter = work.component(usage='record.exporter.deleter')
            return deleter.run(shopware_id)

class ShopwarePropertryLine(models.Model):
    _name = "shopware.property.line"
    _description = 'Shopware Property Line'
    _rec_name = 'attribute_id'

    product_tmpl_id = fields.Many2one('product.template', 'Product Template', ondelete='cascade', required=True)
    attribute_id = fields.Many2one('product.attribute', 'Attribute', ondelete='restrict', required=True)
    value_ids = fields.Many2many('product.attribute.value', string='Attribute Values')

    @api.constrains('value_ids', 'attribute_id')
    def _check_valid_attribute(self):
        # if any(line.value_ids > line.attribute_id.value_ids for line in self):
        #     raise ValidationError(_('Error ! You cannot use this attribute with the following value.'))
        return True

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    shopware_bind_ids = fields.One2many(
        comodel_name='shopware.product.template',
        inverse_name='openerp_id',
        string='Shopware Bindings',
    )

    def export_multi_to_shopware(self, active_ids=False, context=False):
        shopware_data = []
        shopware_ids = []
        products = self.env['product.template'].browse(active_ids)
        for product in products:
            for pp_bind in product.shopware_bind_ids:
                if len(active_ids) == 1:
                    pp_bind.with_delay().export_record()
                else:
                    data = pp_bind.batch_json_export_record()
                    data["id"] = pp_bind.shopware_id
                    shopware_ids.append(pp_bind.shopware_id)
                    shopware_data.append(data)
            product.export_to_shopware()
        if len(active_ids) > 1:
            for product in products:
                for pp_bind in product.shopware_bind_ids:
                    pp_bind.batch_export_record(ids=shopware_ids, data=shopware_data)
                    break
                break

    def export_multi_to_shopware_xmlrpc(self):
        '''
        This method created only for xmlrpc call if user wants to export bunch of product on shopware then we can call this method using xmlrpc
        :return:
        '''
        for product in self:
            for pp_bind in product.shopware_bind_ids:
                pp_bind.with_delay().export_record()
            product.export_to_shopware()
        return True

    def _add_domain_field(self):
        categ_obj = self.env['product.category'].search([('shopware_bind_ids.shopware_id', '>', 0)])
        if categ_obj:
            domain = [('id', 'in', categ_obj.ids)]
        else:
            domain = [('id', '=', -1)]
        return domain
    has_shopware_variants = fields.Boolean(string="Shopware Variants ?")
    shopware_property_ids = fields.One2many('shopware.property.line', 'product_tmpl_id', 'Shopware Property')
    property_set_id = fields.Many2one('property.set', string="Property Set")
    property_set_attribute_ids = fields.Many2many(related='property_set_id.product_attribute_ids', string="Property Attribute")
    status_on_shopware = fields.Boolean(string="Status on Shopware", track_visibility='onchange')
    shopware_meta_title = fields.Char(string='Meta Title SW', copy=True)
    shopware_meta_keyword = fields.Text(string='Meta Keyword', copy=True)
    shopware_meta_description = fields.Text(string='Meta Description SW', copy=True)
    shopware_description = fields.Html(string='Description SW', copy=True)
    is_shopware_exported = fields.Boolean(string='Is Exported ?', compute='_get_is_shopware_exported')
    shopware_image_ids = fields.One2many(
        comodel_name='odoo.product.image',
        inverse_name='product_tmpl_id',
        string='Shopware Images',
    )
    shopware_categories = fields.Many2many(comodel_name='product.category',
                                   string='Shopware Category', domain=_add_domain_field)

    def _get_is_shopware_exported(self):
        for this in self:
            this.is_shopware_exported = False
            for bind in this.shopware_bind_ids:
                if bind.shopware_id:
                    this.is_shopware_exported = True
                    pass

    def _check_tax_mapping(self):
        if self.taxes_id:
            backends = self.env['shopware.backend'].search([])
            taxes = self.taxes_id.filtered(lambda r: r.company_id.sudo().id == backends.sudo().default_company_id.id)
            shop_taxes = []
            for shop_tax in backends.tax_mapping_ids:
                shop_taxes.append(shop_tax.tax_id.id)
            for tax in taxes:
                if tax.id in shop_taxes:
                    return False
            return "Tax mapping is not available for %s tax. Please add in Shopware backend configuration." % taxes.name
        else:
            return "Tax field is required on Shopware."

    def _check_article_code(self):
        sku_code = self.product_variant_id.default_code if self.product_variant_id.default_code else self.product_variant_id.default_code
        return False if sku_code else "Product SKU(default_code) is required on Shopware."

    def _display_warning(self, warining_list=False):
        for warn in warining_list:
            return True
            #self.env.user.notify_warning(warn, _("Shopware Required Field"), False)

    def _check_required_field_for_shopware(self):
        warning_list = []
        is_tax_mapping = self._check_tax_mapping()
        if is_tax_mapping:
            warning_list.append(is_tax_mapping)
        is_sku = self._check_article_code()
        if is_sku:
            warning_list.append(is_sku)
        self._display_warning(warning_list)
        if warning_list:
            return True

    def export_to_shopware(self):
        self.ensure_one()
        if self._check_required_field_for_shopware():
            return True
        backends = self.env['shopware.backend'].search([])
        for backend in backends:
            img_binding = backend.create_bindings_for_model(self, 'shopware_bind_ids')
        return True


class ProductProductAdapter(Component):
    _name = 'shopware.product.template.adapter'
    _inherit = 'shopware.adapter'
    _apply_on = 'shopware.product.template'

    _shopware_uri = 'articles/'

    def _call(self, method, api_call, arguments=None):
        try:
            return super(ProductProductAdapter, self)._call(method, api_call, arguments)
        except xmlrpc.client.Fault as err:
            # this is the error in the Shopware API
            # when the product does not exist
            if err.faultCode == 101:
                raise IDMissingInBackend
            else:
                raise

    def read(self, id, attributes=None):
        return self._call('get', '%s%s' % (self._shopware_uri, id), [{}])

    def write(self, id, data):
        """ Update records on the external system """
        if id:
            return self._call('put',self._shopware_uri+id,  data)
        return self._call('put', self._shopware_uri, data)

    def create(self, data):
        return self._call('post', self._shopware_uri, data)

    def delete(self, id):
        return self._call('delete', '%s%s' % (self._shopware_uri, id), [{}])

class ShopwareBindingProductTemplateListener(Component):
    _name = 'shopware.binding.product.template.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['shopware.product.template']

    '''
    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        if record.no_stock_sync:
            return
        inventory_fields = list(
            set(fields).intersection(self.INVENTORY_FIELDS)
        )
        if inventory_fields:
            record.with_delay(priority=20).export_inventory(
                fields=inventory_fields
            )
    '''

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        record.with_delay().export_record()

class OdooProductTemplateListener(Component):
    _name = 'product.template.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['product.template']


    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        if "update_prices_trigger" in fields and len(fields) == 1:  # Added due to magento price trigger. Shopware and Magento use same model for product. ;)
            return True
        for pp_bind in record.shopware_bind_ids:
            run_trigger = pp_bind.backend_id.check_allowed_fields(model_name=record._name, fields=fields)
            if run_trigger:
                pp_bind.with_delay().export_record(fields=fields)

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_unlink(self, record):
        for binding in record.shopware_bind_ids:
            target_shopware_product_id = getattr(binding,'shopware_id')
            if target_shopware_product_id:
                binding.with_delay().export_delete_record(binding.backend_id, target_shopware_product_id)
