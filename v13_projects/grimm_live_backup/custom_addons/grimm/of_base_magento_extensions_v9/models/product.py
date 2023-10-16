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

import copy
from datetime import datetime

from odoo import models, fields, api, tools
from odoo.exceptions import UserError
from odoo.tools import pycompat
from odoo.tools.translate import _

from ..constants import SIMPLE_PRODUCT, CONFIGURABLE_PRODUCT, PRODUCTS_ODOO_MASTER, \
    CATALOG_SEARCH_VISIBILITY, NOT_VISIBLE_INDIVIDUALY, VISIBILITY_ATTR_CODE, NO_IMAGES_SYNC
import odoo.addons.decimal_precision as dp


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    base_default_code = fields.Char(string='Base Internal Reference')
    magento_ptmpl_bind_ids = fields.One2many('magento.product.template', 'openerp_id', string='Magento bindings')
    magento_pp_bind_ids = fields.One2many('magento.product.product', 'ptmpl_openerp_id',
                                          string='Magento product bindings')
    magento_type = fields.Selection(
        selection='_get_magento_types',
        string='Type on Magento',
        default=SIMPLE_PRODUCT,
        required=False,
        help='Type of product on Magento side when it gets exported.'
    )

    image_ids = fields.One2many('product.image', 'product_tmpl_id', string='Images data')
    should_export = fields.Boolean('Should export to Magento?', compute='_compute_should_export')
    textual_attribute_data_ids = fields.One2many(comodel_name='product.textual.attributes.data',
                                                 inverse_name='product_tmpl_id', string='Textual Attributes data',
                                                 copy=True)
    attribute_data_multi_select_ids = fields.One2many(comodel_name='product.attributes.data.multi_select',
                                                      inverse_name='product_tmpl_id',
                                                      string='Multi Select Attributes Data',
                                                      copy=True)
    price_calculation = fields.Selection(
        [('standard', 'Standard'), ('variant_independent', 'Independent prices on variants')],
        string='Price calculation', default='standard', required=True)
    price_calculation_readonly = fields.Boolean(string='Price calculation readonly',
                                                compute='_price_calculation_readonly')

    def _price_calculation_readonly(self):
        for ptmpl in self:
            ptmpl.price_calculation_readonly = ptmpl._calculate_price_config_readonly()

    def _calculate_price_config_readonly(self):
        self.ensure_one()
        return False

    def adjust_variant_prices(self):
        self.ensure_one()

        for pp in self.product_variant_ids:
            pp.write({'variant_price': pp.lst_price})

        return True

    def _compute_should_export(self):
        backends = self.env['magento.backend'].search([('products_sync_type', '=', PRODUCTS_ODOO_MASTER)])

        for ptmpl in self:
            res = False

            for backend in backends:
                if ptmpl.magento_type == CONFIGURABLE_PRODUCT:
                    if not ptmpl.magento_ptmpl_bind_ids.filtered(lambda rec: rec.backend_id.id == backend.id):
                        res = True
                        break

                for pp in ptmpl.product_variant_ids:
                    if not pp.magento_bind_ids.filtered(lambda rec: rec.backend_id.id == backend.id):
                        res = True
                        break

            ptmpl.should_export = res

    def export_to_magento(self):
        self.ensure_one()

        if not self._valid_odoo_and_magento_types(self):
            raise UserError(_("There is no matching magento product type for %s type in Odoo." % (self.type)))

        backends = self.env['magento.backend'].search([('products_sync_type', '=', PRODUCTS_ODOO_MASTER)])

        for backend in backends:
            variants_no_export = False

            if self.magento_type == CONFIGURABLE_PRODUCT:
                config_binding = backend.create_bindings_for_model(self, 'magento_ptmpl_bind_ids')
                config_binding.with_delay().export_record()
                if not config_binding.magento_id:
                    variants_no_export = True

            for pp in self.product_variant_ids:
                backend.with_context(connector_no_export=variants_no_export).create_bindings_for_model(
                    pp, 'magento_bind_ids').with_delay().export_record()

            self._create_images_binds(backend)

        return True

    def export_to_magento_xmlrpc(self, fields):
        self.ensure_one()
        if self.magento_type == CONFIGURABLE_PRODUCT:
            bindings_collection = self.magento_ptmpl_bind_ids
        else:
            # bindings_collection = record.product_variant_ids and record.product_variant_ids[0].magento_bind_ids
            bindings_collection = self.magento_pp_bind_ids

        for binding in bindings_collection:
            if binding.backend_id.products_sync_type != PRODUCTS_ODOO_MASTER or not binding.magento_id:
                continue
            binding.with_delay().export_record(fields=fields)
        return True

    def _create_images_binds(self, backend):
        self.ensure_one()

        if backend.product_images_export_type == NO_IMAGES_SYNC:
            return False

        for img in self.image_ids.filtered(lambda rec: rec.sync_with_magento == True):
            backend.with_context(connector_no_export=True).create_bindings_for_model(img, 'magento_binding_ids')

        if self.magento_type == CONFIGURABLE_PRODUCT:
            for pp in self.product_variant_ids:
                for img in pp.variant_image_ids.filtered(lambda rec: rec.sync_with_magento == True):
                    backend.with_context(connector_no_export=True).create_bindings_for_model(img, 'magento_binding_ids')

    @api.model
    def _get_magento_types(self):
        return [
            (SIMPLE_PRODUCT, 'Simple'),
            (CONFIGURABLE_PRODUCT, 'Configurable'),
        ]

    @api.model
    def get_magento_visibility(self, binding_record):
        backend_id = binding_record.backend_id.id

        if binding_record._name == 'magento.product.product' and binding_record.magento_product_tmpl_id:
            return NOT_VISIBLE_INDIVIDUALY

        visibility_val = None

        for attr_data in binding_record.attribute_data_ids:
            visibility_attr = attr_data.attr_id.magento_binding_ids.filtered(
                lambda
                    rec: rec.magento_code == VISIBILITY_ATTR_CODE and rec.backend_id.id == backend_id and rec.magento_id != False
            )

            if visibility_attr:
                visibility_val = attr_data.value_id.magento_binding_ids.filtered(
                    lambda rec: rec.backend_id.id == backend_id and rec.magento_id != False)
                break

        if not visibility_val:
            return CATALOG_SEARCH_VISIBILITY

        return visibility_val.magento_id

    @api.model
    def _get_matching_odoo_and_magento_types(self):
        res = {
            'service': [],
            'product': ['simple', 'configurable'],
            'consu': ['simple', 'configurable']
        }

        return res

    @api.model
    def _valid_odoo_and_magento_types(self, product):
        type_mappings = self._get_matching_odoo_and_magento_types()
        mapp_data = type_mappings.get(product.type, [])
        res = mapp_data and product.magento_type in mapp_data or False
        return res

    @api.onchange('has_variants')
    def onchange_has_variants(self):
        if self.has_variants:
            self.magento_type = CONFIGURABLE_PRODUCT
        else:
            self.magento_type = SIMPLE_PRODUCT

    @api.onchange('attribute_set_id')
    def onchange_attribute_set(self):
        # self.attribute_line_ids = False
        self.attribute_data_multi_select_ids = False
        self.textual_attribute_data_ids = False
        if self.attribute_set_id:
            attribute_data = []
            textual_attribute_data = []
            attribute_data_multi_select = []
            for attribute in self.attribute_set_id.product_attribute_ids:
                if not attribute.use_in_products:
                    continue
                if attribute.type in ['select', 'configurable', 'boolean']:
                    # {u'attribute_data_ids': [[0, False, {u'attr_id': 305, u'value_id': 1701}]]}
                    """
                    res = self.env['product.attribute.value'].search([('attribute_id', '=', attribute.id)])
                    if res:
                        attribute_data.append([0, 0, {u'attr_id': attribute.id, u'value_id': res[0].id}])
                    """
                    attribute_data.append([0, 0, {'attr_id': attribute.id}])
                elif attribute.type in ['multiselect', ]:
                    attribute_data_multi_select.append([0, 0, {'attr_id': attribute.id}])
                elif attribute.type in ['text', 'simple_text']:
                    textual_attribute_data.append([0, 0, {'attr_id': attribute.id}])

            if attribute_data or attribute_data_multi_select or textual_attribute_data:
                self.update(
                    {'attribute_data_ids': attribute_data, 'textual_attribute_data_ids': textual_attribute_data,
                     'attribute_data_multi_select_ids': attribute_data_multi_select})
                setattr(self, 'technical_specifications',False)
                setattr(self, 'technical_specifications', attribute_data + attribute_data_multi_select + textual_attribute_data)
                # self.attribute_data_ids = attribute_data

    @staticmethod
    def remove_empty_attribute_value(vals):
        vals_tmp = copy.deepcopy(vals)
        for attribute in vals_tmp.get('attribute_data_ids', []):
            if attribute and attribute[0] == 0 and (not attribute[-1] or not attribute[-1].get('value_id', None)):
                vals['attribute_data_ids'].remove(attribute)
        for attribute in vals_tmp.get('textual_attribute_data_ids', []):
            if attribute and attribute[0] == 0 and (not attribute[-1] or not attribute[-1].get('value_id', None)):
                vals['textual_attribute_data_ids'].remove(attribute)
        for attribute in vals_tmp.get('attribute_data_multi_select_ids', []):
            if attribute and attribute[0] == 0 and (not attribute[-1] or not attribute[-1].get('value_ids', None)):
                vals['attribute_data_multi_select_ids'].remove(attribute)
        return vals

    @api.model
    def create(self, vals):
        vals = self.remove_empty_attribute_value(vals)
        if vals.get('has_variants'):
            vals['magento_type'] = CONFIGURABLE_PRODUCT
        elif vals.get('magento_type', False) == CONFIGURABLE_PRODUCT:
            vals['magento_type'] = SIMPLE_PRODUCT

        res = super(ProductTemplate, self).create(vals)

        if not self._context.get('skip_image_update', False):
            pass
            # deprecated
            # res._ptmpl_adjust_automatic_imgs(vals)
        if 'price_calculation' in vals and vals.get('price_calculation','') == 'standard':
            res.adjust_variant_prices()

        return res

    def write(self, vals):
        vals = self.remove_empty_attribute_value(vals)
        if 'attribute_line_ids' in vals:
            self = self.with_context(skip_product_removal=True)

        res = super(ProductTemplate, self).write(vals)

        if not self._context.get('skip_image_update', False):
            pass
            # deprecated
            # self._ptmpl_adjust_automatic_imgs(vals)

        if vals.get('price_calculation', '') == 'standard':
            for ptmpl in self:
                ptmpl.adjust_variant_prices()

        return res

    def _calculate_price_config_readonly(self):
        self.ensure_one()
        res = not self.has_variants or self.magento_type != CONFIGURABLE_PRODUCT
        return res

    @api.model
    def remove_bindings(self, record, remove_type):
        assert remove_type in ('all', 'empty')

        record_id = record.id

        if record._name == 'product.template':
            if record.magento_type == CONFIGURABLE_PRODUCT:
                table_name = 'magento_product_template'
            else:
                table_name = 'magento_product_product'
                record = record.with_context(active_test=False)
                record_id = record.product_variant_ids and record.product_variant_ids[0].id or None
        else:
            table_name = 'magento_product_product'

        if not record_id:
            return False

        bindings_remove_query = """
                                DELETE FROM %s
                                WHERE openerp_id=%s
                                """ % (table_name, record_id)

        if remove_type == 'empty':
            bindings_remove_query += """ AND magento_id IS NULL"""

        bindings_remove_query += ";"
        self.env.cr.execute(bindings_remove_query)
        return True

    def _check_input_args_validity(self, **kwargs):
        return kwargs.get('is_standard', False)

    @api.model
    def _extract_automatic_image_data_from_PT(self, product_template, **kwargs):
        is_standard = kwargs.get('is_standard', False)

        img_name = 'No IMG'
        image_binary_data = False

        if is_standard:
            img_name = 'Standard - %s' % (product_template.name)
            image_binary_data = product_template.image

        images_collection = product_template.image_ids

        return {
            'image_name': img_name,
            'image_binary_data': image_binary_data,
            'images_collection': images_collection
        }

    @api.model
    def _extract_automatic_image_data_from_PP(self, product_product, **kwargs):
        is_standard = kwargs.get('is_standard', False)

        img_name = 'No IMG'
        image_binary_data = False

        if is_standard:
            img_name = 'Standard - %s' % (product_product.name)
            image_binary_data = product_product.image_variant

        images_collection = product_product.variant_image_ids

        return {
            'image_name': img_name,
            'image_binary_data': image_binary_data,
            'images_collection': images_collection
        }

    @api.model
    def _extract_automatic_image_data_from_product(self, product, **kwargs):
        res = {}

        valid_data = self._check_input_args_validity(**kwargs)

        if not valid_data:
            return False

        if product._name == 'product.template':
            res = self._extract_automatic_image_data_from_PT(product, **kwargs)

        elif product._name == 'product.product':
            res = self._extract_automatic_image_data_from_PP(product, **kwargs)

        return res

    @api.model
    def _search_for_existing_image(self, images_collection, **kwargs):
        is_standard = kwargs.get('is_standard', False)

        res = images_collection.filtered(lambda img: img.is_standard == is_standard)

        return res

    @api.model
    def _check_if_standard_and_prepare_import(self, images_collection, **kwargs):
        is_standard = kwargs.get('is_standard', False)

        if is_standard:
            images_collection.write({'is_base_image': False, 'is_small_image': False, 'is_thumbnail': False})

        return True

    @api.model
    def _prepare_new_image_data(self, product, **kwargs):

        image_name = kwargs.get('image_name')
        is_standard = kwargs.get('is_standard')

        new_image_data = {
            'name': image_name,
            'product_tmpl_id': product.id if product._name == 'product.template' else False,
            'variant_product_id': product.id if product._name == 'product.product' else False,
            'is_base_image': is_standard,
            'is_small_image': is_standard,
            'is_thumbnail': is_standard,
            'is_standard': is_standard,
        }

        if is_standard:
            new_image_data['sequence'] = 1

        return new_image_data

    @api.model
    def _prepare_image_update_data(self, product, **kwargs):
        res = {}

        updated_binary = kwargs.get('updated_binary', False)

        if updated_binary:
            res['binary_write_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        return res

    # deprecated
    @api.model
    def adjust_automatic_image(self, product, **kwargs):

        product_img_data = self._extract_automatic_image_data_from_product(product, **kwargs)

        if not product_img_data:
            return False

        image_name = product_img_data['image_name']
        image_binary = product_img_data['image_binary_data']
        images_collection = product_img_data['images_collection']

        existing_images = self._search_for_existing_image(images_collection, **kwargs)

        if len(existing_images) > 0:

            if not image_binary:
                existing_images.unlink()
            else:
                img_update_vals = self._prepare_image_update_data(product, **kwargs)

                if img_update_vals:
                    existing_images.write(img_update_vals)

        elif image_binary:
            self._check_if_standard_and_prepare_import(images_collection, **kwargs)

            kwargs.update({'image_name': image_name})
            new_image_data = self._prepare_new_image_data(product, **kwargs)

            image = self.env['product.image'].create(new_image_data)

        return True

    # deprecated
    def _ptmpl_adjust_automatic_imgs(self, vals):
        for product in self:
            if 'image' in vals:
                self.adjust_automatic_image(product, is_standard=True, updated_binary=True)
        return True

    @api.constrains('has_variants')
    def _check_configurable_attrs(self):
        if 'create_product_product' in self.env.context or self.env.context.get('create_product_product', False):
            return True

        if self.has_variants:
            variant_attributes = self.attribute_line_ids.filtered(
                lambda rec: rec.attribute_id and len(rec.value_ids) > 0)

            if not variant_attributes:
                raise UserError(_("""You must select configurable attributes and values (under 'Variants' tab)
                                     for product that contains variants!"""))

    @api.constrains('image_ids')
    def _check_image_types(self):
        base_imgs_num = len(self.image_ids.filtered(lambda img: img.is_base_image == True))
        small_imgs_num = len(self.image_ids.filtered(lambda img: img.is_small_image == True))
        thumb_imgs_num = len(self.image_ids.filtered(lambda img: img.is_thumbnail == True))

        msg = ''

        if base_imgs_num > 1:
            msg += _('Product can have only one base image! \n')

        if small_imgs_num > 1:
            msg += _('Product can have only one small image! \n')

        if thumb_imgs_num > 1:
            msg += _('Product can have only one thumbnail image! \n')

        if msg:
            raise UserError(msg)

    def button_remove_all_bindings(self):
        return self.remove_bindings(self, 'all')

    def button_remove_empty_bindings(self):
        return self.remove_bindings(self, 'empty')

    @api.model
    def get_config_only_fields_to_export(self):
        return ['base_default_code', 'attribute_data_ids']

    @api.model
    def get_ptmpl_fields_to_export(self):
        return [
            'name', 'base_default_code', 'default_code', 'active', 'list_price', 'description_sale', 'description'
                                                                                                     'weight',
            'categ_id', 'categ_ids', 'attribute_data_ids', 'textual_attribute_data_ids'
        ]

    @api.model
    def get_storeview_specific_fields(self):
        return [
            'description_sale', 'name'
        ]

    @api.model
    def get_pp_fields_to_export(self):
        return ['default_code', 'lst_price', 'active', 'product_template_attribute_value_ids', 'update_prices_trigger'] #Odoo13Change


class ProductProduct(models.Model):
    _inherit = 'product.product'

    variant_image_ids = fields.One2many(comodel_name='product.image', inverse_name='variant_product_id',
                                        string='Variant images')
    variant_price = fields.Float(string='Variant price', digits='Product Price', default=0,
                                 readonly=True)

    def _set_image_value(self, value):
        if isinstance(value, pycompat.text_type):
            value = value.encode('ascii')
        image = tools.image_resize_image_big(value)
        # change
        if self.product_tmpl_id.has_variants and self.product_tmpl_id.magento_type == CONFIGURABLE_PRODUCT:
            self.image_variant = image
        else:
            self.product_tmpl_id.image = image

    def _adjust_automatic_imgs_pp(self, vals):
        ptmpl_obj = self.env['product.template']
        image_fields = ('image_variant',)

        for product in self:
            if product.product_template_attribute_value_ids: #Odoo13Change
                for img_field in image_fields:
                    if img_field in vals:
                        ptmpl_obj.adjust_automatic_image(product=product, is_standard=True, updated_binary=True)
                        break

        return True

    @api.model
    def create(self, vals):
        res = super(ProductProduct, self).create(vals)

        if not self._context.get('skip_image_update', False):
            res._adjust_automatic_imgs_pp(vals)

        return res

    def write(self, vals):
        res = super(ProductProduct, self).write(vals)

        if not self._context.get('skip_image_update', False):
            self._adjust_automatic_imgs_pp(vals)

        return res

    def unlink(self):
        if self._context.get('skip_product_removal', False):
            res = self.write({'active': False})
        else:
            res = super(ProductProduct, self).unlink()

        return res

    def _prepare_specific_binding_vals(self, backend):
        self.ensure_one()
        return {
            'product_type': SIMPLE_PRODUCT
        }

    def button_remove_all_bindings(self):
        return self.env['product.template'].remove_bindings(self, 'all')

    def button_remove_empty_bindings(self):
        return self.env['product.template'].remove_bindings(self, 'empty')

    @api.model
    def get_child_product_translatable_fields(self):
        """Translatable fields for variant products during import.
           Only fields of product.product model should be set here, because translations for product.template fields
           will be imported during configurable product import."""

        return []


class ProductTextualAttributesData(models.Model):
    _name = 'product.textual.attributes.data'
    _description = 'Product textual attributes data'
    _inherit = 'product.attributes.data'

    is_required = fields.Boolean(related='attr_id.is_required')
    value_id = fields.Text(string='Textual value', translate=True)


class MagentoProductProduct(models.Model):
    _inherit = 'magento.product.product'

    ptmpl_openerp_id = fields.Many2one(
        'product.template',
        related='openerp_id.product_tmpl_id',
        string='Openerp ptmpl ID',
        store=True
    )

    magento_product_tmpl_id = fields.Many2one(
        'magento.product.template',
        compute='_compute_magento_product_tmpl_id',
        string='Magento product template',
        ondelete='cascade',
        store=True
    )

    magento_attribute_set_id = fields.Many2one(
        'magento.product.attribute.set',
        compute='_compute_magento_attribute_set',
        store=True,
        string='Magento attribute set'
    )

    magento_attribute_value_ids = fields.Many2many(
        'magento.product.attribute.value',
        compute='_get_magento_attribute_value_ids',
        string='Magento attribute values'
    )

    magento_categ_ids = fields.Many2many(
        'magento.product.category',
        compute='_get_magento_categ_ids',
        string='Magento product categories'
    )

    magento_category_id = fields.Many2one(
        'magento.product.category',
        compute='_get_magento_category_id',
        store=True,
        string='Magento category'
    )

    arbitrary_magento_ctg_id = fields.Many2one(
        'magento.product.category',
        string='Arbitrary magento category',
        help="""This field is used to set magento category in case when Odoo product category has more than one binding per Magento backend."""
    )

    magento_image_ids = fields.One2many('magento.product.image', 'magento_product_id', string='Magento images',
                                        readonly=True)

    is_variant_on_magento = fields.Boolean('Variant on Magento?', compute='_compute_magento_product_tmpl_id',
                                           store=True)

    @api.depends('openerp_id', 'openerp_id.product_template_attribute_value_ids', 'openerp_id.product_template_attribute_value_ids.magento_binding_ids') #Odoo13Change
    def _get_magento_attribute_value_ids(self):
        for mpp in self:
            res = []

            for attr_val in mpp.product_template_attribute_value_ids: #Odoo13Change
                for attr_val_bind in attr_val.magento_binding_ids.filtered(
                        lambda rec: rec.backend_id.id == mpp.backend_id.id):
                    res.append(attr_val_bind.id)
                    break

            mpp.magento_attribute_value_ids = res

    @api.depends('openerp_id', 'openerp_id.product_tmpl_id', 'openerp_id.product_tmpl_id.magento_ptmpl_bind_ids')
    def _compute_magento_product_tmpl_id(self):

        for mpp in self:
            res = False
            is_variant = False

            for ptmpl_bind in mpp.product_tmpl_id.magento_ptmpl_bind_ids.filtered(
                    lambda rec: rec.backend_id.id == mpp.backend_id.id):
                res = ptmpl_bind.id
                is_variant = True

            mpp.magento_product_tmpl_id = res
            mpp.is_variant_on_magento = is_variant

    @api.depends('openerp_id', 'openerp_id.product_tmpl_id.categ_ids')
    def _get_magento_categ_ids(self):
        for mpp in self:
            res = []

            for categ in mpp.categ_ids:
                for categ_bind in categ.magento_bind_ids.filtered(lambda rec: rec.backend_id.id == mpp.backend_id.id):
                    res.append(categ_bind.id)
                    break

            mpp.magento_categ_ids = res

    @api.depends('openerp_id', 'arbitrary_magento_ctg_id', 'openerp_id.product_tmpl_id.categ_id',
                 'openerp_id.product_tmpl_id.categ_id.magento_bind_ids')
    def _get_magento_category_id(self):
        for mpp in self:
            res = False

            if mpp.arbitrary_magento_ctg_id and mpp.arbitrary_magento_ctg_id.backend_id.id == mpp.backend_id.id and \
                    mpp.arbitrary_magento_ctg_id.openerp_id.id == mpp.categ_id.id:

                res = mpp.arbitrary_magento_ctg_id.id
            else:

                for categ_bind in mpp.categ_id.magento_bind_ids.filtered(
                        lambda rec: rec.backend_id.id == mpp.backend_id.id):
                    res = categ_bind.id

            mpp.magento_category_id = res

    @api.depends('openerp_id', 'openerp_id.attribute_set_id', 'openerp_id.attribute_set_id.magento_binding_ids')
    def _compute_magento_attribute_set(self):
        for mpp in self:
            res = False
            for attr_set_bind in mpp.attribute_set_id.magento_binding_ids.filtered(
                    lambda rec: rec.backend_id.id == mpp.backend_id.id
            ):
                res = attr_set_bind.id
                break

            mpp.magento_attribute_set_id = res

    _sql_constraints = [
        ('backend_oe_uniq', 'unique(backend_id, openerp_id)',
         'Odoo product can be linked with only one product per Magento backend!'),
    ]


class MagentoProductTemplate(models.Model):
    _name = 'magento.product.template'
    _description = 'Magento Product Template'
    _inherit = 'magento.binding'
    _inherits = {'product.template': 'openerp_id'}

    openerp_id = fields.Many2one('product.template', 'Configurable product', required=True, ondelete='cascade')

    magento_product_variant_ids = fields.One2many(
        'magento.product.product',
        'magento_product_tmpl_id',
        string='Magento product variants'
    )

    magento_attribute_set_id = fields.Many2one(
        'magento.product.attribute.set',
        compute='_compute_magento_attribute_set',
        store=True,
        string='Magento attribute set'
    )

    magento_categ_ids = fields.Many2many(
        'magento.product.category',
        compute='_get_magento_categ_ids',
        string='Magento product categories'
    )

    magento_category_id = fields.Many2one(
        'magento.product.category',
        compute='_get_magento_category_id',
        store=True,
        string='Magento category'
    )

    arbitrary_magento_ctg_id = fields.Many2one(
        'magento.product.category',
        string='Arbitrary magento category',
        help="""This field is used to set magento category in case when Odoo product category has more than one binding per Magento backend."""
    )

    magento_image_ids = fields.One2many('magento.product.image', 'magento_ptmpl_id', string='Magento images',
                                        readonly=True)

    no_stock_sync = fields.Boolean(string='No Stock Synchronization for variants', required=False,
                                   help="Check this to exclude the variant products from stock synchronizations.")

    manage_stock = fields.Selection(
        selection=[('use_default', 'Use Default Config'), ('no', 'Do Not Manage Stock'), ('yes', 'Manage Stock')],
        string='Manage Stock Level on Variants', default='use_default', required=True)

    backorders = fields.Selection(
        selection=[('use_default', 'Use Default Config'),
                   ('no', 'No Sell'),
                   ('yes', 'Sell Quantity < 0'),
                   ('yes-and-notification', 'Sell Quantity < 0 and '
                                            'Use Customer Notification')],
        string='Manage Inventory Backorders on variants',
        default='use_default',
        required=True,
    )

    website_ids = fields.Many2many(comodel_name='magento.website', string='Websites', readonly=True)
    created_at = fields.Date('Created At (on Magento)', readonly=True)
    updated_at = fields.Date('Updated At (on Magento)', readonly=True)

    def write(self, vals):
        res = super(MagentoProductTemplate, self).write(vals)

        fields_to_pass = ['no_stock_sync', 'manage_stock', 'backorders']
        vals_fields = list(vals.keys())
        intersect = list(set(fields_to_pass).intersection(vals_fields))

        if intersect:
            vals_to_pass = {}
            for field_name in intersect:
                vals_to_pass[field_name] = vals[field_name]

            res = self.magento_product_variant_ids.write(vals_to_pass)

        return res

    @api.depends('openerp_id', 'openerp_id.attribute_set_id', 'openerp_id.attribute_set_id.magento_binding_ids')
    def _compute_magento_attribute_set(self):
        for mpt in self:
            res = False
            for attr_set_bind in mpt.attribute_set_id.magento_binding_ids.filtered(
                    lambda rec: rec.backend_id.id == mpt.backend_id.id
            ):
                res = attr_set_bind.id
                break

            mpt.magento_attribute_set_id = res

    @api.depends('openerp_id', 'openerp_id.categ_ids.magento_bind_ids')
    def _get_magento_categ_ids(self):
        for mpp in self:
            res = []

            for categ in mpp.categ_ids:
                for categ_bind in categ.magento_bind_ids.filtered(lambda rec: rec.backend_id.id == mpp.backend_id.id):
                    res.append(categ_bind.id)
                    break

            mpp.magento_categ_ids = res

    @api.depends('openerp_id', 'arbitrary_magento_ctg_id', 'openerp_id.categ_id',
                 'openerp_id.categ_id.magento_bind_ids')
    def _get_magento_category_id(self):
        for mpp in self:
            res = False

            if mpp.arbitrary_magento_ctg_id and mpp.arbitrary_magento_ctg_id.backend_id.id == mpp.backend_id.id and \
                    mpp.arbitrary_magento_ctg_id.openerp_id.id == mpp.categ_id.id:
                res = mpp.arbitrary_magento_ctg_id.id
            else:
                for categ_bind in mpp.categ_id.magento_bind_ids.filtered(
                        lambda rec: rec.backend_id.id == mpp.backend_id.id):
                    res = categ_bind.id

            mpp.magento_category_id = res

    _sql_constraints = [
        ('backend_oe_uniq', 'unique(backend_id, openerp_id)',
         'Odoo configurable product can be linked with only one configurable product per Magento backend!'),
    ]


class MagentoProductCategory(models.Model):
    _inherit = 'magento.product.category'

    magento_ctg_name = fields.Char('Magento category name')

    @api.depends('magento_ctg_name', 'openerp_id.name')
    def name_get(self):
        result = []
        for magento_ctg in self:
            res = magento_ctg.magento_ctg_name if magento_ctg.magento_ctg_name else magento_ctg.name
            result.append((magento_ctg.id, '%s (%s)' % (res, magento_ctg.magento_id or '')))

        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if 'product_binding_id' in self.env.context and 'product_binding_model' in self.env.context:
            if not self.env.context['product_binding_id'] or not self.env.context['product_binding_model']:
                return []

            binding_id = self.env.context['product_binding_id']
            binding_model = self.env.context['product_binding_model']
            product_bind = self.env[binding_model].browse(binding_id)
            category = product_bind.categ_id

            if not category or not category.magento_bind_ids:
                return []

            args = [('openerp_id', '=', category.id), ('backend_id', '=', product_bind.backend_id.id)]

        return super(MagentoProductCategory, self).name_search(name=name, args=args, operator=operator, limit=limit)


class ProductsImportHistory(models.Model):
    _name = 'products.import.history'
    _description = 'Products import history'

    backend_id = fields.Many2one('magento.backend', string='Backend', required=True)
    configurable = fields.Text('Configurable products')
    configurable_failed = fields.Text('Failed configurable')
    variant = fields.Text('Variant products')

    def update_history(self, field_name, product_id):
        self.ensure_one()

        if not self[field_name]:
            field_val = str(product_id)
        else:
            field_val = self[field_name] + ',%s' % (str(product_id))

        res = self.write({field_name: field_val})
        return res

    def exists_in_history(self, field_name, product_id):
        self.ensure_one()

        if not self[field_name]:
            return False

        product_history_ids = self[field_name]
        product_history_ids = list(set([int(el) for el in product_history_ids.split(',')]))

        res = int(product_id) in product_history_ids
        return res

    def check_and_remove_from_history(self, field_name, product_id):
        self.ensure_one()
        product_ids = self.get_list_of_ids(field_name)
        res_ids = [str(id) for id in product_ids if id != int(product_id)]
        res_ids = ','.join(res_ids)
        res = self.write({field_name: res_ids})
        return res

    def get_list_of_ids(self, field_name):
        self.ensure_one()

        if not self[field_name]:
            return []

        product_history_ids = self[field_name]
        res = list(set([int(el) for el in product_history_ids.split(',')]))
        return res
