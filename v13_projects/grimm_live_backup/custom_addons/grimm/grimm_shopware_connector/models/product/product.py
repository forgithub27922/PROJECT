#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  config.py
#
#  Copyright 2015 D.H. Bahr <dhbahr@gmail.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#

from odoo import api, fields, models, tools, _
from odoo.tools import float_compare, pycompat
from datetime import datetime
from datetime import timedelta

class AccessoryPartProduct(models.Model):
    _inherit = 'accessory.part.product'

    connect_shopware = fields.Boolean("Shopware", compute="_check_on_shopware")
    connect_magento = fields.Boolean("Magento", compute="_check_on_magento")
    ptmpl_connect_magento = fields.Boolean(related='accessory_part_id.should_export')
    ptmpl_connect_shopware = fields.Boolean(related='accessory_part_id.is_shopware_exported')

    @api.depends('accessory_part_id')
    def _check_on_shopware(self):
        for record in self:
            if record.accessory_part_id:
                is_shopware = self.env['shopware.product.template'].search(
                    [('openerp_id', '=', record.accessory_part_id.id)], limit=1, )
                record.connect_shopware = True if is_shopware else False

    @api.depends('accessory_part_id')
    def _check_on_magento(self):
        for record in self:
            if record.accessory_part_id:
                is_magento = self.env['magento.product.product'].search([('ptmpl_openerp_id', '=', record.accessory_part_id.id)],limit=1,)
                record.connect_magento = True if is_magento else False

class SparePartProduct(models.Model):
    _name = 'spare.part.product'
    _description = 'Spare Part and Quantity'

    spare_part_id = fields.Many2one('product.template', string='Sparepart Product')
    product_id = fields.Many2one('product.template', string='Related Product')
    position = fields.Integer('Position', default=0)
    connect_shopware = fields.Boolean("Shopware", compute="_check_on_shopware")
    connect_magento = fields.Boolean("Magento", compute="_check_on_magento")
    ptmpl_connect_magento = fields.Boolean(related='spare_part_id.should_export')
    ptmpl_connect_shopware = fields.Boolean(related='spare_part_id.is_shopware_exported')

    @api.depends('spare_part_id')
    def _check_on_shopware(self):
        for record in self:
            record.connect_shopware = False
            if record.spare_part_id:
                is_shopware = self.env['shopware.product.template'].search(
                    [('openerp_id', '=', record.spare_part_id.id)], limit=1, )
                record.connect_shopware = True if is_shopware else False

    @api.depends('spare_part_id')
    def _check_on_magento(self):
        for record in self:
            record.connect_magento = False
            if record.spare_part_id:
                is_magento = self.env['magento.product.product'].search(
                    [('ptmpl_openerp_id', '=', record.spare_part_id.id)], limit=1, )
                record.connect_magento = True if is_magento else False

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_device = fields.Boolean("Is product a device ?")

    spare_part_prod_ids = fields.One2many('spare.part.product', 'product_id', string='Spare Parts')

    def _check_brand(self):
        '''
        Brand sync to Manufacture on shopware and Manufacturer is required fiel for product creation on Shopware.
        :return:
        '''
        return "Product %s field is required on shopware."%self.fields_get('product_brand_id').get('product_brand_id').get('string') if not self.product_brand_id else False

    def _check_required_field_for_shopware(self):
        warn_list = []
        super(ProductTemplate, self)._check_required_field_for_shopware()
        is_brand = self._check_brand()
        if is_brand:
            warn_list.append(is_brand)
        self._display_warning(warn_list)
        return True if warn_list else False
