# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Dipak Suthar
#    Copyright 2019 Grimm Gastrobedarf.de
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging
import base64
from odoo import models, fields, api, exceptions, _
from odoo import tools, api
from tempfile import TemporaryFile, NamedTemporaryFile
from odoo.exceptions import UserError
import os.path
import csv

MAX_POP_MESSAGES = 50

_logger = logging.getLogger(__name__)


class ProductMergeLine(models.TransientModel):
    _name = "product.merge.line"
    _description = 'Product Merge Line'


    product_id = fields.Many2one('product.product', 'Product', ondelete='cascade', required=True)
    merge_id = fields.Many2one('product.merge', 'Product', ondelete='cascade', required=True)
    value_ids = fields.Many2many('product.attribute.value', string='Attribute Values')


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    def name_get(self):
        result = []
        for attribute in self:
            if self._context.get("display_techname", False):
                result.append((attribute.id, "%s (%s)"%(attribute.name, attribute.technical_name)))
            else:
                result.append((attribute.id, attribute.name))
        return result

class ProductMerge(models.TransientModel):
    _name = 'product.merge'
    _description = 'Shop Product Merge'

    product_id = fields.Many2one(
        'product.template',
        string='Template Product',
        help="""This is template product all variant will be assign under this product."""
    )
    upload_info = fields.Html("Upload Information", readonly=True)
    attribute_ids = fields.Many2many(comodel_name='product.attribute', string="Property Attribute")

    merge_lines = fields.One2many('product.merge.line', 'merge_id', 'Merge ID')

    def get_attribute_lines(self):
        attr_vals = {}
        for line in self.merge_lines:
            for value in line.value_ids:
                temp_list = attr_vals.get(value.attribute_id.id, [])
                temp_list.append(value.id)
                attr_vals[value.attribute_id.id] = temp_list
        for k, v in attr_vals.items():
            exist_line = self.product_id.attribute_line_ids.filtered(lambda rec: rec.attribute_id.id==k)
            if exist_line:
                v.extend(exist_line.value_ids._ids)
                exist_line.with_context(no_variant_create=True).value_ids = [(6, 0, v)]
            else:
                self.env["product.template.attribute.line"].with_context(no_variant_create=True).create({'product_tmpl_id':self.product_id.id,'attribute_id': k, 'value_ids': [(6, 0, v)]})
        return True

    def get_product_template_attribute_value_ids(self, line):
        val_ids = []
        for val in line.value_ids:
            value_data = self.env["product.template.attribute.value"].search([('product_tmpl_id', '=', line.merge_id.product_id.id),('product_attribute_value_id', '=', val.id), ('attribute_id', '=', val.attribute_id.id)], limit=1)
            if value_data:
                val_ids.extend(value_data.ids)
            else:
                exist_line = self.product_id.attribute_line_ids.filtered(lambda rec: rec.attribute_id.id == val.attribute_id.id)
                if exist_line:
                    new_id = self.env["product.template.attribute.value"].create({
                        'product_tmpl_id':line.merge_id.product_id.id,
                        'product_attribute_value_id': val.id,
                        'attribute_id': val.attribute_id.id,
                        'attribute_line_id': exist_line[0].id,
                    })
                    val_ids.append(new_id.id)
        return val_ids

    def assign_related_model(self):
        product_tmpl_ids = self.mapped('merge_lines.product_id.product_tmpl_id')
        pt_ids = product_tmpl_ids.ids
        pt_ids.append(0)
        tmpl_ids = self.mapped('merge_lines.product_id.product_tmpl_id.id')
        tmpl_ids.append(0)
        self._cr.execute("UPDATE product_supplierinfo SET product_tmpl_id=%s WHERE product_tmpl_id IN %s " % (self.product_id.id, tuple(tmpl_ids)))
        _logger.info("Updated supplier info for child product ===> %s" % self.mapped('merge_lines.product_id.name'))

        for img in product_tmpl_ids.image_ids.filtered(lambda r: r.is_standard):
            if img.product_tmpl_id:
                img_data = img.product_tmpl_id.image_1920
            elif img.variant_product_id:
                img_data = img.variant_product_id.image_1920
            img.write({'is_standard':False, 'manual_image_data':img_data})

        self._cr.execute("UPDATE product_image SET product_tmpl_id=null,variant_product_id=(SELECT product_product.id FROM product_product WHERE product_product.product_tmpl_id=product_image.product_tmpl_id limit 1) WHERE product_image.product_tmpl_id IN " + str(tuple(pt_ids)) + ";")
        _logger.info("Updated Product Image info for child product ===> %s" % self.mapped('merge_lines.product_id.name'))

    def _check_validation(self):
        total_prod_id = []
        total_val_id = []
        for line in self.merge_lines:
            total_prod_id.append(line.product_id.id)
            total_val_id.append(','.join([str(i) for i in sorted(line.value_ids.ids)]))
        if total_prod_id:
            if len(total_prod_id) != len(list(set(total_prod_id))):
                raise UserError(_("You can't assign same artikle multiple time."))
        if total_val_id:
            if len(total_val_id) != len(list(set(total_val_id))):
                raise UserError(_("You can't assign same attribute value in different artikle."))

    def start_assignment(self):
        # self._check_validation()
        # Taking backup from tempate data
        list_price = self.product_id.list_price
        default_code = self.product_id.default_code

        # Template_ids for all product from merge line
        product_tmpl_ids = self.mapped('merge_lines.product_id.product_tmpl_id')

        need_to_delete_p_id = False # If this is newly master product we will use to remove default variant.
        if len(self.product_id.product_variant_ids) == 1:
            need_to_delete_p_id = self.product_id.product_variant_id.id

        self.assign_related_model() # Assign all other values from variant article like supplierr info, images etc

        self.get_attribute_lines() # Attribute and Attribute value will be assign using this method

        for line in self.merge_lines:
            # if line.product_id.product_template_attribute_value_ids:
            #     raise UserError(_('%s .. product is already variant article. Please remove all attribute.' % line.product_id.name))
            val_ids = self.get_product_template_attribute_value_ids(line)

            line.product_id.write({"delete_shopware_product":True}) # We wanted to delete those article from shopware. In new export everything will be new.
            line.product_id.product_tmpl_id.button_remove_shopware6_all_bindings()
            line.product_id.with_context(no_variant_create=True).product_template_attribute_value_ids = [(6, 0, val_ids)]

        self._cr.commit()
        line_prod_ids = self.mapped('merge_lines.product_id.id')
        line_prod_ids.append(0)

        # # Update accessory part relation.
        # self._cr.execute(
        #     "UPDATE %s SET product_id=%s WHERE product_id in (select product_tmpl_id from product_product where id in %s) " % (
        #         'accessory_part_product', self.product_id.id, tuple(line_prod_ids)))
        #
        # # Update Spare part relation.
        # self._cr.execute(
        #     "UPDATE %s SET product_id=%s WHERE product_id in (select product_tmpl_id from product_product where id in %s) " % (
        #         'spare_part_product', self.product_id.id, tuple(line_prod_ids)))
        #
        # # Update Service part relation.
        # self._cr.execute(
        #     "UPDATE %s SET product_id=%s WHERE product_id in (select product_tmpl_id from product_product where id in %s) " % (
        #         'service_part_product', self.product_id.id, tuple(line_prod_ids)))


        # assigning simple category to template categories.
        if need_to_delete_p_id:
            self.product_id.template_shopware6_category_ids = [(6, 0,self.product_id.shopware6_category_ids._ids)]

        self._cr.execute("UPDATE %s SET product_tmpl_id=%s WHERE id in %s " % ('product_product', self.product_id.id, tuple(line_prod_ids)))
        self._cr.commit()
        if need_to_delete_p_id:
            specification_ids = self.product_id.product_variant_id.technical_specifications.ids
            template_short_description = self.product_id.product_variant_id.short_description
            #self._cr.execute("DELETE FROM product_product WHERE id=%s" % (need_to_delete_p_id))
            self._cr.execute("UPDATE product_product SET active='f' WHERE id=%s" % (need_to_delete_p_id))

            self.product_id.product_variant_id.short_description = template_short_description
            if specification_ids:
                specification_ids.append(0)
                self._cr.execute("UPDATE product_template_specifications SET product_tmpl_id=%s WHERE id IN %s " % (self.product_id.product_variant_id.id, tuple(specification_ids)))
        # for variant in self.product_id.product_variant_ids:
        #     if variant.id not in self.mapped('merge_lines.product_id.id'):
        #         variant.unlink()

        self.product_id.write({"base_default_code": "%s-BASE" % default_code, "list_price":list_price, "default_code": self.product_id.product_variant_id.id, "variant_id": self.product_id.product_variant_id.id})

        # for variant in self.product_id.product_variant_ids:
        #     variant.write({"delete_shopware_product":True}) # We wanted to delete those article from shopware. In new export everything will be new.

        product_tmpl_ids.unlink()
        # for pt in product_tmpl_ids:
        #     pt.button_remove_shopware6_all_bindings() # Removing all binding data
        #     pt.unlink() # Finally unlink in odoo

class ProductProduct(models.Model):
    _inherit = 'product.product'

    delete_shopware_product = fields.Boolean(string="Delete product")


