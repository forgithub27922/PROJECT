# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2017 Openfellas (http://openfellas.com) All Rights Reserved.
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

from odoo import models, fields, api, tools
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    customer_comment = fields.Text('Customer comment')
    shop_payment_ref = fields.Char('Shop Payment ref #')

    @api.model
    def create(self, vals):
        result = super(SaleOrder, self).create(vals)
        if result.partner_shipping_id:
            shipping_id = result.partner_shipping_id
            if shipping_id.country_id and shipping_id.country_id.code == "AT":
                result.carrier_id = 4 # Hard coded Austria for delivery method.
        return result


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    height = fields.Float('Height', related='product_id.height', readonly=True)
    width = fields.Float('Width', related='product_id.width', readonly=True)
    depth = fields.Float('Depth', related='product_id.depth', readonly=True)
    connection_ids = fields.One2many(
        'product.connection', 'product_id', string='Connections', related='product_id.product_tmpl_id.connection_ids',
        readonly=True)


    @api.model
    def create(self, vals):
        result = super(SaleOrderLine, self).create(vals)
        return result
        #Due to fiscal position setup no use of this code.
        if result.order_id.partner_shipping_id:
            shipping_id = result.order_id.partner_shipping_id
            if result.order_id.company_id.id == 1:
                if shipping_id.country_id and shipping_id.country_id.code in ["AT", "CZ", "LU"] and shipping_id.vat:
                    result.tax_id = [(6, 0, [7])]
                #else:
                #    result.tax_id = [(6, 0, [12])]
            if result.order_id.company_id.id == 3:
                if shipping_id.country_id and shipping_id.country_id.code in ["AT", "CZ", "LU"] and shipping_id.vat:
                    result.tax_id = [(6, 0, [21])]
                #else:
                #    result.tax_id = [(6, 0, [24])]
        return result


class SaleOrderImportMapper(Component):
    _name = 'magento.sale.order.mapper'
    _inherit = 'magento.sale.order.mapper'
    _apply_on = 'magento.sale.order'

    @mapping
    def payment_ref(self, record):
        if record.get('payment',False):
            #Payment from Payone
            if record.get('payment').get('payone_clearing_reference',False):
                return {'shop_payment_ref':str(record.get('payment').get('payone_clearing_reference',False))}
            # Payment from Amazon
            if record.get('payment').get('ext_order_id',False):
                return {'shop_payment_ref':str(record.get('payment').get('ext_order_id',False))}
            # Payment from Payone
            if record.get('payment').get('last_trans_id',False):
                return {'shop_payment_ref':str(record.get('payment').get('last_trans_id',False))}

    @mapping
    def shipping_method(self, record):
        ifield = record.get('shipping_method')
        if not ifield:
            return

        carrier = self.env['delivery.carrier'].search(
            [('magento_code', '=', ifield)],
            limit=1,
        )
        if carrier:
            result = {'carrier_id': carrier.id}
        else:
            # FIXME: a mapper should not have any side effects
            product = self.env.ref(
                'connector_ecommerce.product_product_shipping')
            carrier = self.env['delivery.carrier'].create({
                'product_id': product.id,
                'name': ifield,
                'magento_code': ifield})
            result = {'carrier_id': carrier.id}
        shipping_address = record.get('shipping_address', False)
        if shipping_address:
            shipping_country_code = shipping_address.get('country_id', False)
            if shipping_country_code and shipping_country_code == "AT":
                result = {'carrier_id': 4}
            elif shipping_country_code and shipping_country_code == "DE":
                result = result
            else:
                result = {'carrier_id': 11}
        return result