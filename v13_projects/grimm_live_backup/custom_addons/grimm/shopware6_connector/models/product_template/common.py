# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
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

_logger = logging.getLogger(__name__)

class Shopware6ProductTemplate(models.Model):
    _name = 'shopware6.product.template'
    _inherit = 'shopware6.binding'
    _inherits = {'product.template': 'openerp_id'}
    _description = 'Shopware6 Product'


    openerp_id = fields.Many2one(comodel_name='product.template',
                                 string='Product',
                                 required=True,
                                 ondelete='restrict')

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    shopware6_pt_bind_ids = fields.One2many('shopware6.product.template', 'openerp_id', string='Shopware6 bindings')
    variant_id = fields.Many2one('product.product', 'Product', compute='_compute_variant_id', store=True)
    shopware6_bind_ids = fields.One2many(related='variant_id.shopware6_bind_ids', string = "Shopware6 product bindings")
    product_media_ids = fields.One2many(string='Product Media', related='variant_id.product_media_ids', readonly=False)
    sales_channel_ids = fields.Many2many(string='Sales Channels', related='variant_id.sales_channel_ids', readonly=False)
    shopware6_category_ids = fields.Many2many(string='Shopware Categories', related='variant_id.shopware6_category_ids',readonly=False, copy=True)
    config_setting = fields.Char("Config JSON")
    shopware6_version_id = fields.Char(string='Shopware6 Version', related='variant_id.shopware6_version_id')

    product_tmpl_media_ids = fields.One2many(
        comodel_name='product.media',
        inverse_name='product_tmpl_id',
        string='Product Template Media',
    )

    @api.model
    def create(self, vals):
        res = super(ProductTemplate, self).create(vals)

        fields_to_write = ['shopware6_bind_ids', 'product_media_ids', 'sales_channel_ids', 'shopware6_category_ids', 'shopware6_version_id', 'technical_specifications', 'main_categ_id', 'short_description', 'prod_name']
        related_vals = {}

        for f in fields_to_write:
            if vals.get(f, False):
                related_vals[f] = vals[f]

        if related_vals:
            res.write(related_vals)

        return res

    @api.depends('product_variant_ids','attribute_line_ids','name')
    def _compute_variant_id(self):
        for p in self:
            p.variant_id = p.product_variant_ids[:1].id

    def export_multi_to_shopware6(self, active_ids=False, context=False):
        products = self.env['product.template'].browse(active_ids)
        for product in products:
            if product.shopware6_bind_ids or product.shopware6_pt_bind_ids:
                fields = ['product_brand_id','technical_specifications','width','is_package','shopware6_delivery_time_id','ean_number','rrp_price','meta_description','search_words','grimm_product_custom_product_template_id','default_code','short_description', 'description', 'technical_specifications', 'channel_ids', 'taxes_id', 'attribute_line_ids', 'shopware6_category_ids', 'image_ids']
                for binding in product.shopware6_bind_ids:
                    binding.with_delay(priority=14).export_record(fields=fields)
                for binding in product.shopware6_pt_bind_ids:
                    binding.with_delay(priority=14).export_record(fields=fields)
                for variant in product.product_variant_ids:
                    for bind in variant.shopware6_bind_ids:
                        bind.with_delay(priority=14).export_record(fields=fields)
            else:
                val = product.export_to_shopware6()
        # return True

    def export_to_shopware6(self):
        self.ensure_one()
        for product in self:
            backends = self.env['shopware6.backend'].search([])
            for backend in backends:
                if product.product_variant_count != 1:
                    product_tmpl_bind = backend.create_bindings_for_model(product, 'shopware6_pt_bind_ids')
                for variant in product.product_variant_ids:
                    product_bind = backend.create_bindings_for_model(variant, 'shopware6_bind_ids')
        return True

    def button_remove_shopware6_all_bindings(self):
        self.ensure_one()
        self.shopware6_pt_bind_ids.unlink()
        for variant in self.product_variant_ids:
            variant.shopware6_bind_ids.unlink()
            for media in variant.product_media_ids:
                media.shopware6_bind_ids.unlink()
            for media in variant.variant_image_ids:
                media.shopware6_bind_ids.unlink()
                media.shopware6_media_file_bind_ids.unlink()
        for media in self.image_ids:
            media.shopware6_bind_ids.unlink()
            media.shopware6_media_file_bind_ids.unlink()
        self._cr.execute("update product_product set cross_selling_id=null where product_tmpl_id=%s"%self.id)
        self._cr.execute("update product_product set shopware6_main_categ_id=null where product_tmpl_id=%s"%self.id)
        self.config_setting = ""
        return {
            'effect': {
                'fadeout': 'slow',
                'message': _("Congrats ! you removed all Shopware bindings."),
                'type': 'rainbow_man',
            }
        }


    def export_multi_to_shopware_xmlrpc(self):
        '''
        This method created only for xmlrpc call if user wants to export bunch of product on shopware6 then we can call this method using xmlrpc
        :return:
        '''
        for product in self:
            for pp_bind in product.shopware6_bind_ids:
                pp_bind.with_delay().export_record()
            product.export_to_shopware()
        return True

    def export_with_delay_record(self, model='',rec_id=False, fields=[], priority=11):
        binding_model = self.env[model].browse(rec_id)
        if binding_model:
            binding_model.with_delay(priority=priority).export_record(fields=fields)
        return "Great Job"

    has_shopware_variants = fields.Boolean(string="Shopware6 Variants ?")
    #shopware_property_ids = fields.One2many('shopware6.property.line', 'product_tmpl_id', 'Shopware6 Property')
    #property_set_id = fields.Many2one('property.set', string="Property Set")
    #property_set_attribute_ids = fields.Many2many(related='property_set_id.product_attribute_ids', string="Property Attribute")
    status_on_shopware = fields.Boolean(string="Status on Shopware6", track_visibility='onchange')
    shopware_meta_title = fields.Char(string='Meta Title SW', copy=True)
    shopware_meta_keyword = fields.Text(string='Meta Keyword', copy=True)
    shopware_meta_description = fields.Text(string='Meta Description SW', copy=True)
    shopware_description = fields.Html(string='Description SW', copy=True)
    is_shopware6_exported = fields.Boolean(string='Is Exported ?', compute='_get_is_shopware6_exported')
    # shopware_image_ids = fields.One2many(
    #     comodel_name='odoo.product.image',
    #     inverse_name='product_tmpl_id',
    #     string='Shopware6 Images',
    # )
    shopware_categories = fields.Many2many(comodel_name='product.category',
                                   string='Shopware6 Category')

    def _get_is_shopware6_exported(self):
        for this in self:
            this.is_shopware6_exported = False
            if this.product_variant_count > 1:
                for bind in this.shopware6_pt_bind_ids:
                    if bind.shopware6_id:
                        this.is_shopware6_exported = True
                        pass
            else:
                for bind in this.shopware6_bind_ids:
                    if bind.shopware6_id:
                        this.is_shopware6_exported = True
                        pass

    '''
    def _check_tax_mapping(self):
        if self.taxes_id:
            backends = self.env['shopware6.backend'].search([])
            taxes = self.taxes_id.filtered(lambda r: r.company_id.sudo().id == backends.sudo().default_company_id.id)
            shop_taxes = []
            for shop_tax in backends.tax_mapping_ids:
                shop_taxes.append(shop_tax.tax_id.id)
            for tax in taxes:
                if tax.id in shop_taxes:
                    return False
            return "Tax mapping is not available for %s tax. Please add in Shopware6 backend configuration." % taxes.name
        else:
            return "Tax field is required on Shopware6."

    def _check_article_code(self):
        sku_code = self.product_variant_id.default_code if self.product_variant_id.default_code else self.product_variant_id.default_code
        return False if sku_code else "Product SKU(default_code) is required on Shopware6."

    def _display_warning(self, warining_list=False):
        for warn in warining_list:
            self.env.user.notify_warning(warn, _("Shopware6 Required Field"), False)

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
    '''



class Shopware6ProductAdapter(Component):
    _name = 'shopware6.product.product.adapter'
    _inherit = 'shopware6.adapter'
    _apply_on = ['shopware6.product.product','shopware6.product.template']

    _shopware_uri = 'api/v3/product/'

    def search(self, filters=None):
        """ Search records according to some criterias
        and returns a list of ids

        :rtype: list
        """
        if not filters:
            filters = ''

        result = self._call('GET','%s?%s' % (self._shopware_uri,filters),{})
        return result.get('data', result)

    def read(self, id, attributes=""):
        """ Returns the information of a record

        :rtype: dict
        """
        result =self._call('GET', '%s%s%s' % (self._shopware_uri, id, attributes), [{}])
        return result.get('data', result)

    def get_config_setting(self, id):
        """ Returns the information of a record

        :rtype: dict
        """
        result = self._call('GET', '%s%s/configurator-settings' % (self._shopware_uri, id), [{}])
        return result.get('data', result)

    def get_children(self, id):
        """ Returns the information of a record

        :rtype: dict
        """
        result = self._call('GET', '%s%s/children' % (self._shopware_uri, id), [{}])
        return result.get('data', result)

    def write(self, id, data):
        """ Update category on the Shopware6 system """
        return self._call('PATCH', '%s%s' % (self._shopware_uri, id), data)

    def delete(self, id):
        return self._call('DELETE', '%s%s' % (self._shopware_uri, id), [{}])

    def create(self, data):
        return self._call('POST', self._shopware_uri, data)

    def mass_update_product(self, data):
        return self._call('POST', "api/_action/sync", data)

    def assign_channels(self, id, data):
        return self._call('POST', self._shopware_uri + id + "/visibilities", data)

    def get_assign_channels(self, id):
        result = self._call('GET', self._shopware_uri + id + "/visibilities")
        return result.get('data', result)

    def del_assign_channels(self, id):
        return self._call('DELETE', "api/v3/product-visibility/" + id)

    def get_assign_categories(self, id):
        result = self._call('GET', self._shopware_uri + id + "/categories")
        return result.get('data', result)

    def del_assign_categories(self, prod_id, categ_id):
        return self._call('DELETE', "%s%s/categories/%s"%(self._shopware_uri,prod_id,categ_id))

class Shopware6BindingProductTemplateListener(Component):
    _name = 'shopware6.binding.product.template.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['shopware6.product.template']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        if record._context.get("export_now", False):
            record.export_record()
        else:
            record.with_delay().export_record()


class Shopware6ProductTemplateListener(Component):
    _name = 'shopware6.product.template.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['product.template']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):

        if "update_prices_trigger" in fields and len(fields) == 1:  # Added due to magento price trigger. Shopware and Magento use same model for product. ;)
            return True

        direct_fields = ['meta_description', 'package_id', 'description_sale', 'warranty_type', 'width', 'ean_number',
                         'manufacture_code', 'weight', 'grimm_product_custom_product_template_id', 'default_code',
                         'height', 'length', 'used_in_manufacturer_listing', 'short_description',
                         'shopware6_category_ids', 'is_spare_part', 'taxes_id', 'meta_title', 'supplier_taxes_id',
                         'search_words', 'shopware6_delivery_time_id', 'name', 'attribute_line_ids', 'is_package',
                         'product_brand_id', 'description', 'rrp_price', 'shopware_active', 'warranty']
        for bind in record.shopware6_bind_ids:
            if all(field in direct_fields for field in fields):
                existing_record = self.env['product.mass.update.queue'].search([('product_id', '=', record.variant_id.id),('is_done', '=', False)])
                if existing_record:
                    field_list = json.loads(existing_record.updated_fields)
                    field_list.extend(fields)
                    existing_record.updated_fields = json.dumps(list(set(field_list)))
                else:
                    self.env['product.mass.update.queue'].create({'product_id': record.variant_id.id, 'updated_fields': json.dumps(fields)})
            else:
                bind.with_delay(description="Export %s product to Shopware"%record.default_code or "").export_record(fields=fields) # Transfer only one variant
        for bind in record.shopware6_pt_bind_ids:
            bind.with_delay(description="Export %s product to Shopware"%record.default_code or "").export_record(fields=fields) #Transfer main template in multi variant

        if record.shopware6_pt_bind_ids:
            backends = self.env['shopware6.backend'].search([])
            for backend in backends:
                for variant in record.product_variant_ids:
                    product_bind = backend.create_bindings_for_model(variant, 'shopware6_bind_ids')
                    #product_bind.with_delay().export_record(fields=fields)