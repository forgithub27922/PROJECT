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

class Shopware6ShoppingPrio(models.Model):
    _name = 'shopware6.shopping.prio'
    _description = 'Shopware6 Shopping Prio'

    name = fields.Char(string="Name", required=True)

class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    related_products = fields.Many2many('product.product', string='Related Products', compute='_compute_related_products')

    def _compute_related_products(self):
        self._cr.execute("select product_tmpl_id from product_template_specifications where id in (select attribute_id from product_attribute_value_product_template_specifications_rel where value_id=%s)" % (self.id))
        product_ids = [x[0] for x in self._cr.fetchall()]
        self.related_products = [(6, 0, product_ids)]

class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    display_in_product_filter = fields.Boolean(string="Shopware6 Product Filter")
    display_on_product_detail_page = fields.Boolean(string="Shopware6 Product Detail Page")
    shopware6_description = fields.Text(string="Shopware6 Description")
    display_type = fields.Selection(string='Display Type', selection=[('text', 'Text'),('select', 'Select'),('media', 'Media')], default='text')

    related_products = fields.Many2many('product.product', string='Related Products',
                                        compute='_compute_related_products')

    def _compute_related_products(self):
        self._cr.execute("select product_tmpl_id from product_template_specifications where attr_id=%s" % (self.id))
        product_ids = [x[0] for x in self._cr.fetchall()]
        self.related_products = [(6, 0, product_ids)]

class ProductTemplateSpecifications(models.Model):
    _name = 'product.template.specifications'
    _description = 'Product Technical Specifications'

    attr_id = fields.Many2one('product.attribute', string='Attribute')
    product_tmpl_id = fields.Many2one('product.product', string='Product Template')
    is_required = fields.Boolean(related='attr_id.is_required')
    value_ids = fields.Many2many(comodel_name='product.attribute.value', column1='attribute_id',
                                 column2='value_id',copy=True, string='Values')

class Shopware6SearchKeyword(models.Model):
    _name = 'shopware6.search.keyword'
    _description = 'Shopware6 Search Keyword'

    name = fields.Char('Name', required=True)

class ProductAdvanceFilter(models.Model):
    _name = 'product.advance.filter'
    _description = 'Product Advance Filter'

    name = fields.Char('Filter', required=True)

    def fetch_products(self):
        print("Fetching products...",self.name)
        import ast
        domain = ast.literal_eval(self.name)
        tree_view_id = self.env.ref('product.product_template_tree_view').id
        if domain:
            product_template = self.env['product.template'].sudo().search(domain)
            return {
                "type": "ir.actions.act_window",
                "res_model": "product.template",
                "views": [[tree_view_id, "tree"], [False, "form"]],
                "domain": [['id', 'in', product_template.ids]],
                "name": "Advance Filter Product",
            }

class SaleChannelRel(models.Model):
    _name = 'sales.channel.rel'

    product_id = fields.Many2one(
        'product.template',
        string='Product ID'
    )
    channel_id = fields.Many2one(
        'sales.channel',
        string='Channel ID'
    )
    visiblity = fields.Selection(string='Visiblity', selection=[('30', 'Visible'), ('20', 'Hide in Listngs'), ('10', 'Hide in Listngs and Search')],
                                   required=True,
                                   default='30')

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        new = super(ProductTemplate, self).copy(default=default)
        new.write({"description_sale":self.description_sale,"description":self.description,"grimm_product_custom_product_template_id":self.grimm_product_custom_product_template_id.id})
        # new.description_sale = self.description_sale
        # new.description = self.description
        # new.grimm_product_custom_product_template_id = self.grimm_product_custom_product_template_id
        return new

    def _search_is_this_variant(self, operator, value):
        self._cr.execute("select product_tmpl_id from (select id,product_tmpl_id from product_product where active='t' group by id,product_tmpl_id) as c group by product_tmpl_id having count(product_tmpl_id) > 1;")
        master_article_ids = [x[0] for x in self._cr.fetchall()]
        if operator == "=":
            return [('id', 'in', master_article_ids)]
        else:
            return [('id', 'not in', master_article_ids)]

    @api.depends('product_variant_ids')
    def _compute_is_it_master(self):
        for product in self:
            product.is_this_variant = True if len(product.product_variant_ids) > 1 else False

    @api.depends('image_ids')
    def _compute_last_mage_updated(self):
        self.last_image_updated = False
        for product in self:
            if product.image_ids:
                product.last_image_updated = max(product.mapped("image_ids.write_date"))

    def open_related_media(self):
        self.ensure_one()
        self._cr.execute(
            "select media_id from media_manager_product_product_rel where product_id in (select id from product_product where active='t' and product_tmpl_id=%s)" % (self.id))
        media_ids = [x[0] for x in self._cr.fetchall()]
        view_mode = "tree,form" if len(media_ids) > 1 else "form"

        return {
            'type': 'ir.actions.act_window',
            'name': 'Media Manager',
            'res_model': 'media.manager',
            'view_mode': view_mode,
            'domain': [('id', 'in', media_ids)],
            'views': [[False, 'tree'],[False, 'form']]
        }

    def _compute_shopware6_last_job_state(self):
        binding_id = model_name = False
        self.shopware6_last_job_status = ""
        for tmpl in self:
            prod_ids = tmpl.product_variant_ids.ids #[str(i) for i in tmpl.product_variant_ids.ids]
            if prod_ids:
                prod_ids.append(0)
                self._cr.execute("select id,state,date_created from queue_job where channel='root.shopware6' and model_name ='shopware6.product.product' and rec_id in (select id::text from shopware6_product_product where openerp_id in %s) ORDER BY date_created desc LIMIT 1" % (tuple(prod_ids),))
                job_state = False
                job_date = False
                for res in self._cr.fetchall():
                    job_state = res[1]
                    job_date = res[2]
                if job_state:
                    tmpl.shopware6_last_job_status = job_state
                if job_state:
                    self._cr.execute(
                        "select id from product_mass_update_queue where is_done ='f' and product_id in %s and create_date > '%s' ORDER BY create_date desc LIMIT 1" % (
                        tuple(prod_ids),job_date))
                    mass_update = [x[0] for x in self._cr.fetchall()]
                    if mass_update:
                        tmpl.shopware6_last_job_status = 'Pending in Mass update'

    shopware6_last_job_status = fields.Char('Last Job Status', compute='_compute_shopware6_last_job_state')
    is_this_variant = fields.Boolean('Master Artikle?', compute='_compute_is_it_master', readonly=True, search="_search_is_this_variant")
    last_image_updated = fields.Datetime('Last Image Updated at', compute='_compute_last_mage_updated', readonly=True, store=True)
    cross_selling_title = fields.Char(string='Cross Selling Title', related='variant_id.cross_selling_title')
    shopware6_shopping_prio_id = fields.Many2one('shopware6.shopping.prio',string='Shopping Prio', related='variant_id.shopware6_shopping_prio_id', readonly=False)
    is_accessorypart_cross = fields.Boolean(string='Add Accessory as Cross selling? ', related='variant_id.is_accessorypart_cross', readonly=False)
    is_sparepart_cross = fields.Boolean(string='Add Sparepart as Cross selling? ', related='variant_id.is_sparepart_cross', readonly=False)
    is_servicepart_cross = fields.Boolean(string='Add Servicepart as Cross selling? ', related='variant_id.is_servicepart_cross', readonly=False)
    cross_selling_id = fields.Char(string='Cross Selling Id', related='variant_id.cross_selling_id', readonly=False)
    ecommerce_link = fields.Html(string='E-Commerce link', related='variant_id.ecommerce_link', readonly=True)
    shopware_active = fields.Boolean(string='Active on Shopware ', related='variant_id.shopware_active', readonly=False)
    technical_specifications = fields.One2many(related='variant_id.technical_specifications', string = "Technical Specification", readonly=False, copy=True)
    accessory_part_ids = fields.One2many(related='variant_id.accessory_part_ids', string = "Accessory Parts", readonly=False, copy=True)
    shopware6_delivery_time_id = fields.Many2one('shopware6.delivery.time', string='Shopware6 Delivery Time')
    short_description = fields.Char(string='Short Description', related='variant_id.short_description', translate=False, copy=True, readonly=False)
    template_short_description = fields.Char(string='Template Short Description', translate=False, copy=True, readonly=False)
    prod_name = fields.Char(string='Product Name', related='variant_id.prod_name', translate=False, copy=True, readonly=False)
    shopware6_price_trigger = fields.Boolean(name="Update Prices Trigger Shopware6",
                                           help="Change the values of this field to active product price update to shopware 6", compute='',
                                           default=False, store=False)
    price_on_request = fields.Boolean(string="Price on request", copy=True,
                                      related="product_variant_ids.price_on_request",
                                      help="Set Purchase Price & Sale Price = 9999,99", readonly=False)

    is_special_price_update = fields.Boolean(string="Is Special price update", copy=False, help="This field will be toggle when special price data changed.", readonly=False, default=True)

    channel_ids = fields.One2many(
        comodel_name='sales.channel.rel',
        inverse_name='product_id',
        string='Sales Channel',
    )

    shopware6_sale_unit = fields.Float(string='Sale Unit', related='variant_id.shopware6_sale_unit', readonly=False)
    shopware6_sale_unit_measure = fields.Many2one('shopware6.unit', string="UOM", related='variant_id.shopware6_sale_unit_measure', readonly=False)

    description_sale = fields.Text(
        'Sales Description', translate=True, related='variant_id.description_sale', readonly=False,
        help="A description of the Product that you want to communicate to your customers. "
             "This description will be copied to every Sales Order, Delivery Order and Customer Invoice/Credit Note",copy=True)

    packaging_unit = fields.Char(string='Packaging Unit', related='variant_id.packaging_unit', readonly=False)
    packaging_unit_plural = fields.Char(string='Packaging Unit Plural', related='variant_id.packaging_unit_plural', readonly=False)
    shopware6_base_unit = fields.Float(string='Base Unit', related='variant_id.shopware6_base_unit', readonly=False)

    description = fields.Text('Description', related='variant_id.description', readonly=False, copy=True)
    template_shopware6_category_ids = fields.Many2many(comodel_name='product.category', relation='product_template_product_category_rel', string='Shopware6 Categories For Template')

    tech_attr_name = fields.Char(string="Technical Attribute",related='variant_id.tech_attr_name')
    tech_attr_value_name = fields.Char(string="Technical Attribute Value", related='variant_id.tech_attr_value_name')


    search_words = fields.Many2many(comodel_name='shopware6.search.keyword', column1='product_id',
                                 column2='word_id', copy=True, string='Search Words')

    main_categ_id = fields.Many2one(related='variant_id.main_categ_id', string = "Shopware6 Main Category", readonly=False, copy=True)
    shopware6_main_categ_id = fields.Char(related='variant_id.shopware6_main_categ_id',
                                              string="Shopware6 Main Categotry", readonly=False, copy=True)
    length = fields.Float(related='variant_id.length', string="Length", readonly=False)

    shopware6_product_listing = fields.Selection(string='Product_listing', selection=[('single', 'Single main variant'), ('expand', 'Expand property values in product listings')], default='expand')
    main_variant_id = fields.Many2one('product.product', string='Main Variant')
    parent_product_listing = fields.Boolean(string="Use Parent product in listing")
    dont_show_variant = fields.Boolean(string="Don't show variants")
    show_property = fields.Boolean(string="Show Properties")
    show_value_number = fields.Boolean(string="Show the number of values")
    show_in_cross_selling = fields.Boolean(string="Show in Cross Selling")

    @api.model
    def create(self, vals):
        '''
        Inherited for task OD-1271 (Changing name of product variant, changes name of prodcut.template)
        :param vals:
        :return:
        '''
        if not vals.get("name", False):
            vals["name"] = "Grimm Testing"
        new_product_id = super(ProductTemplate, self).create(vals)
        return new_product_id



    @api.model
    def default_get(self, fields):
        result = super(ProductTemplate, self).default_get(fields)
        channel_ids = []
        for id in self.env['sales.channel'].search([]).ids:
            channel_ids.append((0,0,{'channel_id':id, 'visiblity':'30'}))
        if channel_ids:
            result["channel_ids"] = channel_ids
        return result

    def assign_image_archieved_prod(self):
        self._cr.execute("select id from product_product where product_tmpl_id=%s" % (self.id))
        product_ids = [x[0] for x in self._cr.fetchall()]
        products = self.env["product.product"].browse(product_ids)
        archived_prod = products.filtered(lambda rec: not rec.active)
        active_prod = products.filtered(lambda rec: rec.active)
        avail_prod = {} # Active Product id and all attribute value ids list
        not_avail_prod = {} # Archived Product id and all attribute value ids list
        for prod in active_prod:
            avail_prod[prod] = [v.id for v in prod.product_template_attribute_value_ids]

        for prod in archived_prod:
            not_avail_prod[prod] = [v.id for v in prod.product_template_attribute_value_ids]

        # If new product satisfied all attribute values of archived then assigned it.
        for k,v in not_avail_prod.items():
            for image in k.variant_image_ids:
                for k1,v1 in avail_prod.items():
                    if all(elem in v1 for elem in v) and not k1.variant_image_ids:
                        new_image = image.copy()
                        new_image.variant_product_id = k1.id


    def write(self, vals):
        if any(price_field in vals.keys() for price_field in ['special_price','special_price_from','special_price_to']):
            vals["is_special_price_update"] = True
        res = super(ProductTemplate, self).write(vals)
        fields_to_pass = ['product_media_ids', 'sales_channel_ids', 'shopware6_category_ids', 'shopware6_version_id', 'main_categ_id', 'prod_name']
        vals_fields = list(vals.keys())
        intersect = list(set(fields_to_pass).intersection(vals_fields))
        if intersect:
            vals_to_pass = {}
            for field_name in intersect:
                vals_to_pass[field_name] = vals[field_name]
            res = self.product_variant_ids.write(vals_to_pass)

        if vals.get("name", False): #"Update the varant name if there is only one variant..."
            for this in self:
                if len(this.product_variant_ids) == 1:
                    this.product_variant_id.name = vals.get("name")

        if 'attribute_line_ids' in vals or (vals.get('active') and len(self.product_variant_ids) == 0):
            self.assign_image_archieved_prod()

        if vals.get("description", False):
            for pt in self:
                pt.product_variant_id.description = vals.get("description")
        return res

class ProductSupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    is_related = fields.Boolean(compute='_compute_is_related') # Created field t display related supplier in product view

    def _compute_is_related(self):
        self.is_related = False
        prod_id = self._context.get("PLEASE_FILTER",False)
        if prod_id:
            for rec in self:
                if rec.product_id and rec.product_id.id == prod_id:
                    rec.is_related = True

class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def get_default_channel(self):
        return self.env['sales.channel'].search([]).ids

    def _unlink_or_archive(self, check_access=True):
        """Inherited this method just to archived product instead of unlink
        during variant creation so we can use the image of archived articles.
        """
        if check_access:
            self.check_access_rights('unlink')
            self.check_access_rule('unlink')
            self.check_access_rights('write')
            self.check_access_rule('write')
            self = self.sudo()
            self.write({'active': False})
        # try:
        #     with self.env.cr.savepoint(), tools.mute_logger('odoo.sql_db'):
        #         self.unlink()
        # except Exception:
        #     # We catch all kind of exceptions to be sure that the operation
        #     # doesn't fail.
        #     if len(self) > 1:
        #         self[:len(self) // 2]._unlink_or_archive(check_access=False)
        #         self[len(self) // 2:]._unlink_or_archive(check_access=False)
        #     else:
        #         if self.active:
        #             # Note: this can still fail if something is preventing
        #             # from archiving.
        #             # This is the case from existing stock reordering rules.
        #             self.write({'active': False})

    name = fields.Char(string='Name', readonly=False)
    cross_selling_title = fields.Char(string='Cross Selling Title', readonly=False)
    shopware_active = fields.Boolean(string='Active on Shopware ')
    shopware6_shopping_prio_id = fields.Many2one('shopware6.shopping.prio', string='Shopping Prio')
    is_accessorypart_cross = fields.Boolean(string='Add Accessory as Cross selling? ', readonly=True, default="True")
    is_sparepart_cross = fields.Boolean(string='Add Sparepart as Cross selling? ', readonly=False)
    is_servicepart_cross = fields.Boolean(string='Add Servicepart as Cross selling? ', readonly=False)
    cross_selling_id = fields.Char(string='Cross Selling Id', readonly=False)
    sales_channel_ids = fields.Many2many(comodel_name='sales.channel', relation='product_product_sales_channel_rel',default= get_default_channel)
    ecommerce_link = fields.Html(string='E-Commerce link', compute="_get_ecommerce_link")
    short_description = fields.Char(string='Short Description', translate=False, copy=True)
    prod_name = fields.Char(string='Product Name', translate=False, copy=True)
    technical_specifications = fields.One2many(comodel_name='product.template.specifications',
                                               inverse_name='product_tmpl_id',
                                               string='Technical Specification',
                                               copy=True)
    accessory_part_ids = fields.One2many(
        'accessory.part.product', 'product_id', string='Accessory Parts', copy=True)
    main_categ_id = fields.Many2one('product.category',string="Shopware6 Main Category", copy=True)
    shopware6_main_categ_id = fields.Char(string="Shopware6 Main Category")
    length = fields.Float('Length', copy=True)

    shopware6_sale_unit = fields.Float(string='Sale Unit', readonly=False)
    shopware6_sale_unit_measure = fields.Many2one('shopware6.unit', string="UOM")
    packaging_unit = fields.Char(string='Packaging Unit', readonly=False)
    packaging_unit_plural = fields.Char(string='Packaging Unit Plural', readonly=False)
    shopware6_base_unit = fields.Float(string='Base Unit', readonly=False)

    description_sale = fields.Text(
        'Sales Description', translate=True,
        help="A description of the Product that you want to communicate to your customers. "
             "This description will be copied to every Sales Order, Delivery Order and Customer Invoice/Credit Note", copy=True)

    is_variant_shopware6_exported = fields.Boolean(string='Is Exported ?', compute='_get_is_variant_shopware6_exported')
    description = fields.Text(
        'Description', translate=True,
        help="A precise description of the Product, used only for internal information purposes.",
        track_visibility='onchange', copy=True)
    ecom_categ_id = fields.Many2one('product.category', string='E-commerce Category', help="This field created only for sale reporting. There is no mapping to live shop.",compute='_get_ecom_categ_id', store=True)

    full_details = fields.Char('Product Full Details', compute='_get_full_details', store=True)

    #@api.depends('default_code', 'name')
    def _get_full_details(self):
        for product in self:
            product.full_details = str(product.default_code)+ "===" + str(product.with_context(lang='de_DE').name)+ "===" + str( product.ecom_categ_id.with_context(lang='de_DE').complete_name)

    @api.depends('shopware6_category_ids', 'main_categ_id')
    def _get_ecom_categ_id(self):
        for product in self:
            if product.main_categ_id:
                product.ecom_categ_id = product.main_categ_id
            elif product.shopware6_category_ids:
                product.ecom_categ_id = product.shopware6_category_ids[0]

    @api.depends('technical_specifications')
    def _get_technical_attribute_value(self):
        for product in self:
            attr_name = product.with_context(lang="de_DE").mapped('technical_specifications.attr_id.name')
            attr_value_name = product.with_context(lang="de_DE").mapped('technical_specifications.value_ids.name')
            product.tech_attr_name = ", ".join(attr_name)
            product.tech_attr_value_name = ", ".join(attr_value_name)

    tech_attr_name = fields.Char(string="Technical Attribute", compute='_get_technical_attribute_value', store=True)
    tech_attr_value_name = fields.Char(string="Technical Attribute Value", compute='_get_technical_attribute_value', store=True)

    def _get_is_variant_shopware6_exported(self):
        for this in self:
            this.is_variant_shopware6_exported = False
            for bind in this.shopware6_bind_ids:
                if bind.shopware6_id:
                    this.is_variant_shopware6_exported = True
                    pass

    def export_multi_to_shopware6(self, active_ids=False, context=False):
        products = self.env['product.product'].browse(active_ids)
        for product in products:
            if product.shopware6_bind_ids:
                fields = ['product_brand_id','technical_specifications','width','is_package','shopware6_delivery_time_id','ean_number','rrp_price','meta_description','search_words','grimm_product_custom_product_template_id','default_code','short_description', 'template_short_description', 'description', 'technical_specifications', 'channel_ids', 'taxes_id', 'attribute_line_ids', 'shopware6_category_ids']
                for binding in product.shopware6_bind_ids:
                    binding.with_delay(priority=14).export_record(fields=fields)
            else:
                val = product.product_tmpl_id.export_to_shopware6()
        # return True

    def _get_ecommerce_link(self):
        for this in self:
            front_link = "#"
            back_link = "#"
            if len(this.product_variant_ids) > 1:
                for binding in this.shopware6_pt_bind_ids:
                    if binding.shopware6_id:
                        if this.base_default_code:
                            front_link = "%ssearch?search=%s" % (binding.backend_id.location, this.base_default_code)
                        back_link = "%sadmin#/sw/product/detail/%s/base" % (
                        binding.backend_id.location, binding.shopware6_id)
            else:
                for binding in this.shopware6_bind_ids:
                    if binding.shopware6_id:
                        if this.default_code:
                            front_link = "%ssearch?search=%s"%(binding.backend_id.location,this.default_code)
                        back_link = "%sadmin#/sw/product/detail/%s/base"%(binding.backend_id.location, binding.shopware6_id)

            this.ecommerce_link = "<a href='%s' target='new' class='link-success'>Front End</a><br/><a target='new' href='%s' class='link-success'>Back End</a>"%(front_link,back_link)

    def _update_pack_list_price(self, pt_id):
        product = self.env["product.template"].browse(pt_id)
        if product.cal_pack_price:
            list_price = product.mapped("pack_ids.list_price")
            product.write({"rrp_price":sum(list_price)})

    def write(self, vals):
        '''
        Inherited for task OD-1271 (Changing name of product variant, changes name of prodcut.template)
        :param vals:
        :return:
        '''
        result = super(ProductProduct, self).write(vals)
        for this in self:
            if not this.name and this.product_tmpl_id.name:
                this.name = this.product_tmpl_id.name
            if this.product_tmpl_id.product_variant_count == 1 and not this.product_tmpl_id.name:
                this.product_tmpl_id.name = this.name

        if isinstance(vals, dict) and vals.get("rrp_price", False):
            prod_ids = self.ids
            prod_ids.append(0)
            self._cr.execute("select distinct(bi_product_template) from product_pack where product_id in %s" % str(tuple(prod_ids)))
            product_tmpl_ids = [x[0] for x in self._cr.fetchall()]
            for pt_id in product_tmpl_ids:
                self._update_pack_list_price(pt_id)

        return result

    @api.model
    def create(self, vals):
        '''
        Inherited for task OD-1271 (Changing name of product variant, changes name of prodcut.template)
        :param vals:
        :return:
        '''
        new_product_id = super(ProductProduct, self).create(vals)
        if not new_product_id.name:
            new_product_id.name = new_product_id.product_tmpl_id.name
        if len(new_product_id.product_tmpl_id.product_variant_ids) == 1:
            new_product_id.product_tmpl_id.with_context(connector_no_export=True).name = vals.get("name","")
        return new_product_id


class Shopware6ProductAdapter(Component):
    _inherit = 'shopware6.product.product.adapter'
    _apply_on = ['shopware6.product.product','shopware6.product.template']

    _shopware_uri = 'api/v3/product/'

    def get_assigned_cross_selling(self, id):
        """ Returns the information of a record

        :rtype: dict
        """
        result = self._call('GET', '%s%s/cross-sellings' % (self._shopware_uri, id), [{}])
        return result.get('data', result)

    def get_assigned_cross_selling_products(self,cross_selling_id):
        uri = "api/v3/product-cross-selling/%s/assigned-products"%cross_selling_id
        result = self._call('GET', uri, [{}])
        return result.get('data', result)

    def delete_assigned_product(self,cross_selling_id):
        uri = "api/v3/product-cross-selling-assigned-products/%s"%cross_selling_id
        result = self._call('DELETE', uri, [{}])
        return result.get('data', result)

    def get_assigned_main_category(self,id):
        result = self._call('GET', self._shopware_uri + id + "/main-categories")
        return result.get('data', result)

    def del_assign_main_category(self, id):
        return self._call('DELETE', "api/v3/main-category/" + id)

    def read_proprties(self,product_id):
        uri = "%s%s/properties"%(self._shopware_uri,product_id)
        result = self._call('GET', uri, [{}])
        return result.get('data', result)

    def delete_proprties(self,product_id,property_id):
        uri = "%s%s/properties/%s"%(self._shopware_uri,product_id,property_id)
        result = self._call('DELETE', uri, [{}])
        return result.get('data', result)

    def create_update_cross_selling(self,create_vals,cross_id=False):
        uri = "api/v3/product-cross-selling/"
        method = "POST"
        if cross_id:
            uri += cross_id
            method = "PATCH"
        result = self._call(method, uri, create_vals)
        return result

    def create_update_main_category(self,create_vals,shopware6_id=False):
        uri = "api/v3/main-category/"
        method = "POST"
        if shopware6_id:
            uri += shopware6_id
            method = "PATCH"
        result = self._call(method, uri, create_vals)
        return result

    def assign_product(self,data):
        uri = "api/v3/product-cross-selling-assigned-products/"
        return self._call('POST', uri, data)

class Shopware6ProductProductListenerInherit(Component):
    _name = 'shopware6.product.product.listener.inherit'
    _inherit = 'base.connector.listener'
    _apply_on = ['product.template', 'product.product']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_unlink(self, record):
        for binding in record.shopware6_bind_ids:
            target_shopware6_id = getattr(binding, 'shopware6_id')
            # if target_shopware6_id:
            #     binding.with_delay().export_delete_record(binding.backend_id, target_shopware6_id)