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

import logging

from odoo import models, fields, api, _
from odoo.addons.of_base_magento_extensions_v9.constants import SIMPLE_PRODUCT, CONFIGURABLE_PRODUCT
from odoo.exceptions import ValidationError, Warning
from odoo.tools import pycompat

import odoo.addons.decimal_precision as dp
from ..constants import BYERPROTECT_TYPE

_logger = logging.getLogger(__name__)


class ProductMagentoStatus(models.Model):
    _name = 'product.magento.status'
    _description = 'Product magento status'

    name = fields.Char('Name', required=True, translate=True)
    magento_value_map_ids = fields.One2many('product.magento.status.mapping', 'magento_status_id',
                                            'Magento status mappings')

    def get_magento_status_value(self, backend_id):
        self.ensure_one()
        res = None

        for line in self.magento_value_map_ids.filtered(lambda rec: rec.backend_id.id == backend_id):
            res = line.status_magento_attr_value_id

        return res

    @api.model
    def get_odoo_status_id(self, backend_id, magento_id):
        res = False
        mapps = self.env['product.magento.status.mapping'].search(
            [('backend_id', '=', backend_id), ('status_magento_attr_value_id.magento_id', '=', magento_id)]
        )

        if mapps:
            res = mapps[0].magento_status_id

        return res

class SrMultiProduct(models.TransientModel):
    _name = 'sr.multi.product'
    _description = 'SR multi product'

    product_ids = fields.Many2many('product.template', string="Product")

    def add_product(self):
        for line in self.product_ids:
            prod_id = self._context.get('active_id')
            if prod_id:
                product_object = self.env["product.template"].browse(int(prod_id))
                product_object.write({"accessory_part_ids": [(0, 0, {'accessory_part_id': line.id, 'quantity': 0})]})
        return

class AccessoryPartProduct(models.Model):
    _inherit = 'accessory.part.product'

    position = fields.Integer('Position', default=0)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    META_TITLE_MAX_LEN = 65
    META_DESCRIPTION_MAX_LEN = 160

    connection = fields.Text('Connection')
    rrp_price = fields.Float('List Price', related='product_variant_ids.rrp_price', track_visibility="onchange",readonly=False)
    height = fields.Float('Height', related='product_variant_ids.height', copy=True, readonly=False)
    width = fields.Float('Width', related='product_variant_ids.width', copy=True, readonly=False)
    depth = fields.Float('Depth', related='product_variant_ids.depth', copy=True, readonly=False)

    #magento_accessory_ids = fields.Many2many('product.template', 'product_magento_accessory_rel', 'src_id', 'dest_id', string='Magento Accessories')


    magento_product_status_id = fields.Many2one('product.magento.status', string='Status on Magento',
                                                default=lambda self: self._get_default_magento_product_status(),
                                                copy=False, track_visibility='onchange')
    short_description = fields.Char(string='Short Description', translate=False, copy=True)
    special_price = fields.Monetary(string='Special Price', copy=True, digits='Product Price', track_visibility='onchange')
    special_price_from = fields.Datetime(string='Special Price from', help='Special Price from Date', copy=True)
    special_price_to = fields.Datetime(string='Special Price to', help='Special Price to Date', default=None)
    product_link_related_ids = fields.One2many(comodel_name='product.link', inverse_name='linked_product_tmpl_id',
                                               string="Related Products", copy=True, domain=[('type', '=', 'related')])
    product_link_cross_sell_ids = fields.One2many(comodel_name='product.link', inverse_name='linked_product_tmpl_id',
                                                  string="Cross Selling Products", copy=True,
                                                  domain=[('type', '=', 'cross_sell')])
    product_link_up_sell_ids = fields.One2many(comodel_name='product.link', inverse_name='linked_product_tmpl_id',
                                               string="Up Selling Products", copy=True,
                                               domain=[('type', '=', 'up_sell')])

    # meta data
    meta_title = fields.Char(string='Meta Title', copy=True)
    meta_keyword = fields.Text(string='Meta Keyword', copy=True)
    meta_description = fields.Text(string='Meta Description', copy=True)
    meta_autogenerate = fields.Boolean(string='Meta Auto generate', copy=True, help='0 for No; 1 for Yes')
    meta_title_counter = fields.Char(string='Meta Title Counter', compute='_compute_meta_title_counter',
                                     readonly=True, store=False)
    meta_description_counter = fields.Char(string='Meta Description Counter',
                                           compute='_compute_meta_description_counter',
                                           readonly=True, store=False)

    used_in_manufacturer_listing = fields.Integer(string="Show in Manufacturer Listing", copy=True, default=0,
                                                  help='0 or empty - No listing; 1 - First Product, 2 - Second Product, etc.')
    magento_delivery_time = fields.Many2one(string='Magento Delivery Time', comodel_name='product.attribute.value',
                                            domain=[('attribute_id.technical_name', '=', 'grimm_delivery_time')],
                                            default=False, copy=True)

    calculated_magento_price = fields.Monetary(string='Shop Price', help='Calculated Preis for Magento',
                                            related='product_variant_ids.calculated_magento_price')
    magento_visibility = fields.Many2one(string='Magento Visibility', comodel_name='product.attribute.value',
                                         domain=[('attribute_id.technical_name', '=', 'visibility')],
                                         default=False)
    update_prices_trigger = fields.Boolean(name="Update Prices Trigger",
                                           help="Change the values of this field to active product update", compute='',
                                           default=False, store=False)

    def _compute_prices_trigger(self):
        pass

    @staticmethod
    def create_counter_warning(field, max_len):
        diff = max_len - len(field) if field else max_len
        if diff >= 0:
            msg = '%s %s' % (diff, _('character left.'))
        else:
            msg = '%s %s' % (abs(diff), _('character surplus.'))
        return msg

    def export_multi_to_magento(self,active_ids=False,context=False):
        products = self.env['product.template'].browse(active_ids)
        for product in products:
            product.export_to_magento()

    @api.depends('meta_title')
    def _compute_meta_title_counter(self):
        for product_tmpl in self:
            msg = self.create_counter_warning(product_tmpl.meta_title, self.META_TITLE_MAX_LEN)
            product_tmpl.meta_title_counter = msg

    @api.depends('meta_description')
    def _compute_meta_description_counter(self):
        for product_tmpl in self:
            msg = self.create_counter_warning(product_tmpl.meta_description, self.META_DESCRIPTION_MAX_LEN)
            product_tmpl.meta_description_counter = msg

    def tracking_magento_price(self):
        self.ensure_one()
        if len(self.product_variant_ids) == 1:
            return self.product_variant_ids[0].tracking_magento_price()
        raise Warning(
            'Product Template hat multiple Product Variants. Please tracking the price calculation on the Product Variant')

    def tracking_standard_price(self):
        self.ensure_one()
        if len(self.product_variant_ids) == 1:
            return self.product_variant_ids[0].tracking_standard_price()
        raise Warning(
            'Product Template has multiple Product Variants. Please tracking the price calculation on the Product Variant')

    @api.model
    def _get_default_magento_product_status(self):
        res = self.env['product.magento.status'].search([('name', '=', 'Disabled')])
        if res:
            return res.id
        return

    @api.model
    def _get_magento_types(self):
        res = super(ProductTemplate, self)._get_magento_types()
        res.extend([
            (BYERPROTECT_TYPE, 'Trusted shops - byer protection')
        ])
        return res

    @api.model
    def _get_matching_odoo_and_magento_types(self):
        res = super(ProductTemplate, self)._get_matching_odoo_and_magento_types()
        res['service'].append(BYERPROTECT_TYPE)
        return res

    @api.model
    def create(self, vals):
        res = super(ProductTemplate, self).create(vals)

        fields_to_write = ['rrp_price', 'height', 'width', 'depth', 'price_calculation_group']
        related_vals = {}

        for f in fields_to_write:
            if vals.get(f, False):
                related_vals[f] = vals[f]

        if related_vals:
            res.write(related_vals)

        return res

    def write(self, vals):

        res = super(ProductTemplate, self).write(vals)

        if vals.get('magento_product_status_id', False):
            for pt in self.filtered(lambda rec: rec.magento_type == CONFIGURABLE_PRODUCT):
                for pp in pt.product_variant_ids:
                    pp.write({'variant_product_status_id': vals['magento_product_status_id']})
        return res

    @api.model
    def get_config_only_fields_to_export(self):
        res = super(ProductTemplate, self).get_config_only_fields_to_export()
        new_fields = ['connection', 'magento_product_status_id']
        fields_to_remove = []
        res.extend(new_fields)
        res = list(set(res) - set(fields_to_remove))
        return res

    @api.model
    def get_ptmpl_fields_to_export(self):
        res = super(ProductTemplate, self).get_ptmpl_fields_to_export()
        new_fields = ['connection', 'warranty', 'warranty_type', 'product_brand_id', 'magento_product_status_id',
                      'short_description', 'description', 'categ_id', 'categ_ids', 'product_link_related_ids',
                      'product_link_up_sell_ids', 'product_link_cross_sell_ids', 'meta_autogenerate', 'meta_title',
                      'meta_keyword', 'meta_description', 'grimm_delivery_time', 'magento_visibility',
                      'used_in_manufacturer_listing', 'update_prices_trigger', 'rrp_price', 'magento_delivery_time',
                      'textual_attribute_data_ids', 'attribute_data_ids', 'attribute_data_multi_select_ids',
                      'special_price', 'special_price_from', 'barcode',
                      'special_price_to', 'price_calculation_group', 'attribute_set_id','is_package','package_id','accessory_part_ids','spare_part_prod_ids','is_spare_part']
        fields_to_remove = ['description_sale']
        # fields_to_remove = []
        res.extend(new_fields)
        res = list(set(res) - set(fields_to_remove))
        return res

    @api.model
    def get_pp_fields_to_export(self):
        res = super(ProductTemplate, self).get_pp_fields_to_export()
        new_fields = ['rrp_price', 'height', 'width', 'depth', 'variant_product_status_id']
        fields_to_remove = ['lst_price']
        res.extend(new_fields)
        res = list(set(res) - set(fields_to_remove))
        return res

    @api.model
    def get_storeview_specific_fields(self):
        res = super(ProductTemplate, self).get_storeview_specific_fields()
        new_fields = ['connection']
        fields_to_remove = []
        res.extend(new_fields)
        res = list(set(res) - set(fields_to_remove))
        return res

    def update_to_magento(self):
        """
        for record in self:
            if not record._valid_odoo_and_magento_types(record):
                _logger.error(_("There is no matching magento product type for %s type in Odoo." % (record.type)))

        backends = self.env['magento.backend'].search([('products_sync_type', '=', PRODUCTS_ODOO_MASTER)])

        for backend in backends:
            variants_no_export = False

            if self.magento_type == CONFIGURABLE_PRODUCT:
                config_binding = backend.create_bindings_for_model(self, 'magento_ptmpl_bind_ids')
                if not config_binding.magento_id:
                    variants_no_export = True

            for pp in self.product_variant_ids:
                backend.with_context(connector_no_export=variants_no_export).create_bindings_for_model(
                    pp, 'magento_bind_ids')

            self._create_images_binds(backend)
        """
        return True

class shop_price_tracking(models.TransientModel):
    _name = 'shop.price.tracking'
    _description = 'Shop price tracking'

    price_track = fields.Html("Price Tracking")

class ResCompany(models.Model):
    _inherit = 'res.company'

    fax = fields.Char(string='Fax')
    pricelist_id = fields.Many2one("product.pricelist", string="Shop Pricelist", help="This is starting point to calculate shop price.")

class ProductProduct(models.Model):
    _inherit = 'product.product'

    rrp_price = fields.Float('List Price', copy=True, track_visibility="onchange")
    height = fields.Float('Height', copy=True)
    width = fields.Float('Width', copy=True)
    depth = fields.Float('Depth', copy=True)
    variant_product_status_id = fields.Many2one('product.magento.status', string='Status on Magento')
    calculated_magento_price = fields.Monetary(string='Sale Price', help='Calculated Sale Price (for Magento)',
                                            compute='_compute_magento_price')
    update_prices_trigger = fields.Boolean(name="Update Prices Trigger",
                                           help="Change the values of this field to active product update", compute='',
                                           default=False, store=False)

    def _compute_prices_trigger(self):
        pass

    def update_price_history(self, pricelist=None):
        if not pricelist:
            magento_backend = self.env['magento.backend'].search([])
            magento_backend = magento_backend[0] if magento_backend else magento_backend
            pricelist = magento_backend.pricelist_id if magento_backend else None
        res = super(ProductProduct, self).update_price_history(pricelist=pricelist)
        return res

    def _compute_magento_price(self):
        magento_backend = self.env['magento.backend'].search([])
        magento_backend = magento_backend[0] if magento_backend else magento_backend
        job_uuid = self._context.get("job_uuid", False)
        pricelist_user = self._get_session_user()
        pricelist_id = pricelist_user.company_id.pricelist_id
        if not pricelist_id:
            pricelist_id = magento_backend.pricelist_id if magento_backend else None

        for record in self:
            override_price = False
            seller = record.with_context({'product_id': record.id, 'no_special_purchase_price': True,
                                          'force_company': pricelist_user.company_id.id})._select_seller()

            if seller:
                parent_seller = seller.name
                while parent_seller.parent_id:
                    parent_seller = parent_seller.parent_id
                if parent_seller.apply_sale_pricelist:
                    override_price = True

            try:
                magento_price = record.calculated_standard_price
            except:
                magento_price = record.calculated_standard_price
            if override_price:
                magento_price = record._get_extra_price(seller.name,
                                                        getattr(record, parent_seller.sale_base_price),
                                                        'out').get("price")
            else:
                if pricelist_id:
                    product = record.with_context(
                        quantity = 1,
                        pricelist = pricelist_id.id,
                        currency_id = magento_backend.pricelist_id.currency_id.id,
                        uid = pricelist_user.id
                    )
                    try:
                        magento_price = product.price
                    except:
                        magento_price = product.price
                else:
                    magento_price = record.list_price
            record.calculated_magento_price = magento_price


    def _compute_rec_link(self, prod_id, model='product.pricelist.item'):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        database_name = self._cr.dbname
        return '%s/web?db=%s#id=%s&view_type=form&model=%s' % (base_url, database_name, prod_id, model)

    def _get_tracking_message(self, trackings = [], supplier_track = False):
        trackings.reverse()
        current_user = self.env["res.users"].browse(self._context.get("uid", self.env.user.id))
        seller = self.with_context({'no_special_purchase_price': True, 'force_company': current_user.company_id.id})._select_seller()
        seller = seller.name if seller else False
        if seller and seller.parent_id:
            while seller.parent_id:
                seller = seller.parent_id

        base_dict = {'rrp_price': _('List Price'), 'standard_price': _('Purchase Price'),
                     'pricelist': _('Other Pricelist'), 'list_price': _('Public Price')}
        track_info = "<center><table class='table table-striped' width='50%'><thead><tr><th scope='col'>#</th><th scope='col'>Applied pricelist Sequence</th></tr></thead><tbody>"
        if supplier_track:
            apply_pricelist = True if seller and seller.apply_purchase_pricelist else False
        else:
            apply_pricelist = True if seller and seller.apply_sale_pricelist else False
        if apply_pricelist:
            for index, pricelist in enumerate(
                    seller.purchase_pricelist_ids if supplier_track else seller.sale_pricelist_ids):
                if self._is_valid_pricelist(pricelist):
                    track_info += "<tr style='background-color: lavender;'><th scope='row'>" + str(
                        index + 1) + "</th><td><a href='" + self._compute_rec_link(
                        pricelist.id,
                        model='partner.pricelist.item' if supplier_track else 'partner.sale.pricelist.item') + "' target='new'> Pricelist from Supplier - " + pricelist.name if pricelist.name else '' + "</a></td></tr>"
        else:
            for index,track in enumerate(trackings):
                item_id = track.split("@")
                last_pricelist_id = False
                if len(item_id[1].split("_")) > 1:
                    last_pricelist_id = item_id[1].split("_")[1]
                    last_pricelist_id = self.env["product.pricelist"].browse(int(last_pricelist_id))
                if item_id[1].isdigit():
                    item_obj = self.env["product.pricelist.item"].browse(int(item_id[1]))
                    track_info += "<tr style='background-color: beige;'><th scope='row'>"+str(index+1)+"</th><td><a target='new' href='"+self._compute_rec_link(item_obj.id)+"'>"+item_obj.name+" "+item_obj.pricelist_id.name+"</a></td></tr>"
                else:
                    track_info += "<tr style='background-color: beige;'><th scope='row'>" + str(index + 1) + "</th><td><a href='"+self._compute_rec_link(last_pricelist_id.id, model='product.pricelist')+"' target='new'>"+last_pricelist_id.name+"</a> No suitable rule found.</td></tr>"




        track_info += "</tbody></table></center>"

        trackings.reverse()
        track_info += "<center><h2 style='font-weight:bold;color:#009EE3'>Detail Tracking</h2><table class='table table-striped'><thead><tr><th scope='col'>Index</th><th scope='col'>Pricelist</th><th scope='col'>Pricelist's Rule</th><th scope='col'>Based On</th><th scope='col'>Formula</th><th scope='col'>Result</th><th scope='col' style='color:green;'>Marge</th></tr></thead><tbody>"

        if not apply_pricelist:
            convert_to_price_uom = (lambda price: self.uom_id._compute_price(price, self.uom_id))
            for index,track in enumerate(trackings):
                item_id = track.split("@")
                last_pricelist_id = False
                if len(item_id[1].split("_")) > 1:
                    last_pricelist_id = item_id[1].split("_")[1]
                    last_pricelist_id = self.env["product.pricelist"].browse(int(last_pricelist_id))
                price_limit = item_id[0]
                if item_id[1].isdigit():
                    item_obj = self.env["product.pricelist.item"].browse(int(item_id[1]))
                    price_tracking = ""
                    if item_obj.compute_price == 'fixed':
                        price_tracking = u"%s%s" % (price_tracking, item_obj.currency_id.symbol)
                    elif item_obj.compute_price == 'percentage':
                        price_tracking = u"%s%s - %s%%" % (price_tracking, item_obj.currency_id.symbol, item_obj.percent_price)
                    else:
                        price_tracking = u"%s %s %s%%" % (price_tracking, item_obj.percent_sign, item_obj.price_discount)
                        if item_obj.price_round:
                            price_tracking = u"round(%s, rule.price_round)" % price_tracking

                        if item_obj.price_surcharge:
                            price_surcharge = convert_to_price_uom(item_obj.price_surcharge)
                            price_tracking = u"%s + %s%s" % (price_tracking, price_surcharge, item_obj.currency_id.symbol)

                        if item_obj.price_min_margin:
                            price_min_margin = convert_to_price_uom(item_obj.price_min_margin)
                            price_tracking = u"max(%s, %s)" % (price_tracking, price_limit + price_min_margin)

                        if item_obj.price_max_margin:
                            price_max_margin = convert_to_price_uom(item_obj.price_max_margin)
                            price_tracking = u"min(%s, %s)" % (price_tracking, price_limit + price_max_margin)
                    track_info += "<tr style='background-color: beige;'><th scope='row'>"+str(index+1)+"</th><td><a href='"+self._compute_rec_link(item_obj.pricelist_id.id, model='product.pricelist')+"' target='new'>"+item_obj.pricelist_id.name+"</a></td><td><a target='new' href='"+self._compute_rec_link(item_obj.id)+"'>"+item_obj.name+"</a></td><td>"+base_dict.get(item_obj.base, "")+"</td><td>"+ "%.2f" % round(float(price_limit),2)+" "+price_tracking+"</td><td>"+ "%.2f" % round(float(item_id[2]),2)+"</td><td>"+ "%.2f" % round(float(item_id[2])-float(price_limit),2)+"</td></tr>"
                else:
                    track_info += "<tr style='background-color: beige;'><th scope='row'>" + str(index + 1) + "</th><td><a href='"+self._compute_rec_link(last_pricelist_id.id, model='product.pricelist')+"' target='new'>"+last_pricelist_id.name+"</a></td><td>No suitable rule found.</td><td>Sales Price</td><td></td><td>" + "%.2f" % round(self.list_price,2) + "</td></tr>"

                final_price = round(float(item_id[2]),2)
        if apply_pricelist:

            final_price = self.rrp_price if supplier_track else getattr(self,seller.sale_base_price)

            seller_price_track = self._get_extra_price(seller,final_price, 'in' if supplier_track else 'out').get("price_msg")
            for index,msg in enumerate(seller_price_track):
                track_info += "<tr style='background-color: lavender;'><th scope='row'>" + str(
                    index + 1) + "</th><td colspan='3'><a href='" + self._compute_rec_link(msg[0].id,
                                                                               model='partner.pricelist.item' if supplier_track else 'partner.sale.pricelist.item') + "' target='new'>" + str(msg[0].name) + "</a></td><td>" + msg[2] + "</td><td>" + "%.2f" % round(float(msg[-1]),
                                                                                                 2) + "</td><td>" + "%.2f" % round(
                    float(msg[-1]) - float(msg[1]), 2) + "</td></tr>"
                final_price = round(float(msg[-1]),2)


        track_info += "</tbody></table></center>"
        track_info += self._get_final_price_stamp(str("%.2f" % round(float(final_price),2)))
        return track_info


    def _get_final_price_stamp(self, price):
        return "<center>" \
               "<div class='container' style='position: relative; text-align: center; color: white; width:100%;'>" \
               "<img src='/grimm_magentoerpconnect/static/src/img/final_price.png' alt='Snow' style='width:11%;height:11%;'>" \
               "<div class='centered' style='position: absolute;color:#009EE3; top: 50%;left: 50%;transform: translate(-50%, -50%);'>" \
               "<b style='color:red;font-size: initial;'>"+str(price)+"</b></div></div><br/><b style='color:red;font-size: large; font-family: monospace;'>Final Price" \
                                                                      "</b></center>"
    def tracking_magento_price(self):
        self.ensure_one()
        tracking_id = self.env["shop.price.tracking"].create({"price_track":"<h3 style='color:red;'>Price Tracking</h3>"})
        pricelist_user = self.env["res.users"].browse(self._context.get("uid", self.env.user.id))
        pricelist_id = pricelist_user.company_id.pricelist_id
        magento_backend = self.env['magento.backend'].search([])
        if not pricelist_id:
            magento_backend = magento_backend[0] if magento_backend else magento_backend
            pricelist_id = magento_backend.pricelist_id if magento_backend else None
        trackings = []
        if pricelist_id:
            # if getattr(self, "is_pack", False) and getattr(self, "cal_pack_price", False):
            #     current_user = self.env["res.users"].browse(self._context.get("uid", self.env.user.id))
            #     seller = self.with_context(
            #         {'no_special_purchase_price': True, 'force_company': current_user.company_id.id})._select_seller()
            #     parent_seller = seller.name
            #     while parent_seller.parent_id:
            #         parent_seller = parent_seller.parent_id
            #
            #     track_info = "<center><h2>This is pack product so price will be calculated based on pack products.</h2><br/><table class='table table-striped' width='50%'><thead><tr><th scope='col'>#</th><th scope='col'>Product</th><th scope='col'>Shop Price</th><th scope='col'>Quantity</th><th scope='col'>Total</th></tr></thead><tbody>"
            #     final_price = 0
            #     for index,pack_prod in enumerate(self.pack_ids):
            #         final_price = 0
            #         con_product = pack_prod.product_id.with_context(
            #             quantity=1,
            #             pricelist=pricelist_id.id,
            #             currency_id=magento_backend.pricelist_id.currency_id.id,
            #             uid=pricelist_user.id
            #         )
            #         try:
            #             final_price += con_product.price * pack_prod.qty_uom
            #         except:
            #             final_price += con_product.price * pack_prod.qty_uom
            #
            #
            #         #final_price += con_product.price * pack_prod.qty_uom
            #         track_info += "<tr style='background-color: beige;'>" \
            #                       "<th scope='row'>" + str(index + 1) + "</th>" \
            #                       "<td><a href='" + self._compute_rec_link(pack_prod.product_id.id,
            #                                                                        model='product.product') + "' target='new'>" + pack_prod.product_id.name + "</a></td>" \
            #                       "<td>"+str(con_product.price)+"</td>" \
            #                       "<td>"+str(pack_prod.qty_uom)+"</td><td>"+str(con_product.price * pack_prod.qty_uom)+"</td></tr>"
            #
            #     track_info += "<tr style='background-color: beige;'><td colspan='4' style='text-align: right'> <b>Total </b></td> <td>" + str(
            #         round(float(final_price), 2)) + "</td></tr>"
            #     apply_pricelist = True if parent_seller.apply_sale_pricelist else False
            #     if apply_pricelist:
            #         track_info += "<tr><td colspan='5'> Vendor price lists </td></tr>"
            #         for index, pricelist in enumerate(parent_seller.sale_pricelist_ids):
            #             if self._is_valid_pricelist(pricelist):
            #                 track_info += "<tr style='background-color: lavender;'><td colspan='5'><a href='" + self._compute_rec_link(
            #                     pricelist.id,
            #                     model='partner.sale.pricelist.item') + "' target='new'> Pricelist from Supplier - " + pricelist.name if pricelist.name else '' + "</a></td></tr>"
            #
            #         seller_price_track = self._get_extra_price(parent_seller, final_price, 'out').get(
            #             "price_msg")
            #         for index, msg in enumerate(seller_price_track):
            #             track_info += "<tr style='background-color: lavender;'><th scope='row'>" + str(
            #                 index + 1) + "</th><td><a href='" + self._compute_rec_link(msg[0].id,
            #                                                                            model='partner.sale.pricelist.item') + "' target='new'>" + \
            #                           msg[0].name + "</a></td><td>" + msg[2] + "</td><td>" + "%.2f" % round(
            #                 float(msg[-1]),
            #                 2) + "</td><td>" + "%.2f" % round(
            #                 float(msg[-1]) - float(msg[1]), 2) + "</td></tr>"
            #             final_price = round(float(msg[-1]), 2)
            #
            #     track_info += "</tbody></table></center>"
            #     track_info += self._get_final_price_stamp(str("%.2f" % round(float(final_price), 2)))
            #     tracking_id.price_track = track_info
            #
            # else:
            res = pricelist_id.with_context(track = True)._compute_price_rule(list(zip(self, [1] * len(self), [False] * len(self))), flush=True)
            trackings = res[self.id][3]
            track_info = self._get_tracking_message(trackings, supplier_track = False)
            tracking_id.price_track = track_info

        return {
            'name': _('Price Tracking Information'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'shop.price.tracking',
            'res_id': tracking_id.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def tracking_standard_price(self):
        self.ensure_one()

        tracking_id = self.env["shop.price.tracking"].create(
            {"price_track": "<h3 style='color:red;'>Price Tracking</h3>"})
        current_user = self.env["res.users"].browse(self._context.get("uid", self.env.user.id))
        seller = self.with_context({'no_special_purchase_price': True, 'force_company': current_user.company_id.id})._select_seller()
        supplier_pricelist = seller.name.get_supplier_pricelist()
        special_purchase_price = self.get_special_purchase_price()
        parent_seller = seller.name
        while parent_seller.parent_id:
            parent_seller = parent_seller.parent_id

        if getattr(self, "is_pack", False) and getattr(self, "cal_pack_price", False):
            if special_purchase_price is not None:
                price = special_purchase_price
                tracking_id.price_track = "<center><h3 style='color:red;'>Price Tracking</h3><br/><h2>Product has special purchase price.</h2>%s</center>" % self._get_final_price_stamp(price)
            else:
                track_info = "<center><h2>This is pack product so price will be calculated based on pack products.</h2><br/><table class='table table-striped' width='50%'><thead><tr><th scope='col'>#</th><th scope='col'>Product</th><th scope='col'>Purchase Price</th><th scope='col'>Quantity</th><th scope='col'>Total</th></tr></thead><tbody>"
                final_price = 0
                for index, pack_prod in enumerate(self.pack_ids):

                    purchase_price = pack_prod.product_id._get_purchase_price()
                    final_price += purchase_price * pack_prod.qty_uom
                    track_info += "<tr style='background-color: beige;'>" \
                                  "<th scope='row'>" + str(index + 1) + "</th>" \
                                                                        "<td><a href='" + self._compute_rec_link(
                        pack_prod.product_id.id,
                        model='product.product') + "' target='new'>" + pack_prod.product_id.name + "</a></td>" \
                                                                                                   "<td>" + str(
                        purchase_price) + "</td>" \
                                          "<td>" + str(pack_prod.qty_uom) + "</td><td>" + str(
                        purchase_price * pack_prod.qty_uom) + "</td></tr>"

                track_info += "<tr style='background-color: beige;'><td colspan='4' style='text-align: right'> <b>Total </b></td> <td>"+str(round(float(final_price), 2)) +"</td></tr>"
                track_info += "</tbody></table></center>"
                track_info += self._get_final_price_stamp(str("%.2f" % round(float(final_price), 2)))
                tracking_id.price_track = track_info
        else:
            if special_purchase_price is not None:
                price = special_purchase_price
                tracking_id.price_track = "<center><h3 style='color:red;'>Price Tracking</h3><br/><h2>Product has special purchase price.</h2>%s</center>" % self._get_final_price_stamp(price)
            else:
                if supplier_pricelist or parent_seller.apply_purchase_pricelist:
                    trackings = []
                    if supplier_pricelist and not parent_seller.apply_purchase_pricelist:
                        supplier, pricelist_id = supplier_pricelist
                        if pricelist_id:
                            res = pricelist_id.with_context(track=True, standard_price=self.rrp_price,supplier_id=parent_seller.id)._compute_price_rule(
                                list(zip(self, [1] * len(self), [False] * len(self))), flush=True)
                            trackings = res[self.id][3]
                    track_info = self._get_tracking_message(trackings, supplier_track = True)
                    tracking_id.price_track = track_info
                else:
                    tracking_id.price_track = "<center><h3 style='color:red;'>Price Tracking</h3><br/><h2 style='color:red;'>No Pricelist defind for <u><b> %s </b></u>supplier.</h2></center>" % seller.name.display_name

        return {
            'name': _('Price Tracking Information'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'shop.price.tracking',
            'res_id': tracking_id.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def _prepare_specific_binding_vals(self, backend):
        self.ensure_one()
        res = {}

        if self.magento_type in (SIMPLE_PRODUCT, BYERPROTECT_TYPE):
            res['product_type'] = self.magento_type
            return res

        return super(ProductProduct, self)._prepare_specific_binding_vals(backend)


class ProductMagentoStatusMapping(models.Model):
    _name = 'product.magento.status.mapping'
    _description = 'Product magento status mapping'

    magento_status_id = fields.Many2one('product.magento.status', string='Magento status')
    backend_id = fields.Many2one('magento.backend', string='Magento backend')
    status_magento_attr_value_id = fields.Many2one('magento.product.attribute.value', string='Magento attribute value')


class MagentoProductProduct(models.Model):
    _inherit = 'magento.product.product'

    @api.model
    def product_type_get(self):
        res = super(MagentoProductProduct, self).product_type_get()
        res.extend([
            (BYERPROTECT_TYPE, 'Trusted shops - byer protection')
        ])

        return res


class ProductWarrantyType(models.Model):
    _inherit = 'product.warranty.type'

    magento_value_map_ids = fields.One2many('magento.product.warranty.map', 'waranty_type_id',
                                            'Magento warranty mappings')

    def get_magento_warranty_value(self, months, backend_id):
        self.ensure_one()
        res = None

        for line in self.magento_value_map_ids.filtered(lambda rec: rec.months_no == months and
                                                                    rec.magento_attr_value_id and
                                                                    rec.magento_attr_value_id.backend_id.id == backend_id):
            res = line.magento_attr_value_id

        return res


class MagentoProductWarrantyMap(models.Model):
    _name = 'magento.product.warranty.map'
    _description = 'Magento product warranty map'

    waranty_type_id = fields.Many2one('product.warranty.type', string='Product warranty type')
    interval = fields.Selection(selection=[('month', 'Month'), ('year', 'Year')], string='Interval', default='month',
                                required=True, translate=True)

    interval_no = fields.Float('Interval no', default=1, required=True)

    months_no = fields.Float(string='Months no', compute='_calculate_months', store=True)

    magento_attr_value_id = fields.Many2one('magento.product.attribute.value', string='Magento attribute value',
                                            domain=[('magento_id', '!=', False)])

    _sql_constraints = [
        ('attr_value_uniq', 'unique(magento_attr_value_id)',
         'You can not assign same attribute value to more that one mapping!'),
    ]

    @api.depends('interval_no', 'interval')
    def _calculate_months(self):
        for record in self:
            multiplier = 1 if record.interval == 'month' else 12
            record.months_no = record.interval_no * multiplier
