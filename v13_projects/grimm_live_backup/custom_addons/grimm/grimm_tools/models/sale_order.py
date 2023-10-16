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
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, AccessError
from psycopg2 import IntegrityError, OperationalError, errorcodes
from odoo.tools import float_compare, float_round, float_is_zero, pycompat
import logging

_logger = logging.getLogger(__name__)

class ResCurrency(models.Model):
    '''
    Inherited model to remove deprecated method warning.
    '''
    _inherit = "res.currency"
    def compute(self, from_amount, to_currency, round=True):
        # _logger.warning('The `compute` method is deprecated. Use `_convert` instead')
        date = self._context.get('date') or fields.Date.today()
        company = self.env['res.company'].browse(self._context.get('company_id')) or self.env.company
        return self._convert(from_amount, to_currency, company, date)

class DeliveryPartner(models.Model):
    '''
    Inherited model to remove deprecated method warning.
    '''
    _name = "delivery.partner"

    name = fields.Char("Name", required=True)
    track_link = fields.Char("Link", required=True, help="Use %s as as a place holder for link.")

class SaleOrder(models.Model):
    _inherit = "sale.order"

    cancel_reason = fields.Char('Reason for cancellation')
    delivery_partner_id = fields.Many2one("delivery.partner", string="Delivery Partner")
    track_id = fields.Char("Track ID")
    track_link = fields.Html("Link",compute="_get_tracking_url")

    def _get_tracking_url(self):
        self.track_link = ""
        for order in self:
            if order.delivery_partner_id and order.track_id:

                order.track_link = "<a href='{track_shipment}' target='_blank'>Track Shipment</a>".format(track_shipment=order.delivery_partner_id.track_link.replace("%s","{track}").format(track=order.track_id))

    def open_cancel_reasons(self):
        reason = self.env["sale.order.cancel.reason"].search([('sale_order_ids', 'in', [self.id])])
        result = {
            'name': _('Tasks'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'sale.order.cancel.reason',
            "domain": [["id", "in", reason.ids]],
        }
        return result

    def action_cancel_with_reason(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cancel Reason'),
            'res_model': 'sale.order.cancel.reason',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_sale_order_ids': self.ids,'default_type': 'order'},
            'views': [[False, 'form']]
        }

    def action_proforma_cancel_with_reason(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cancel Reason'),
            'res_model': 'sale.order.cancel.reason',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_sale_order_ids': self.ids,'default_type': 'invoice'},
            'views': [[False, 'form']]
        }

    @api.onchange('user_id')
    def onchange_user_id(self):
        res = super(SaleOrder, self).onchange_user_id()
        if self.create_uid.id in [78,1]:
            self.team_id = 2
        return res

    def action_draft(self):
        '''
        Override set to Quotation button method for set invoiced qty to zero for order line.
        :return:
        '''
        res = super(SaleOrder, self).action_draft()
        self.order_line.write({'qty_invoiced': 0})
        return res

    def action_view_purchase(self):
        action = self.env.ref('purchase.purchase_rfq').read()[0]
        # action['domain'] = [('id', 'in', self.mapped('order_line.purchase_line_ids.order_id').ids)] # Old domain only check order id in purchase line.
        #Grimm Start
        action['domain'] = ['|',('id', 'in', self.mapped('order_line.purchase_line_ids.order_id').ids),('origin', 'like', self.name)] # We have added also origin to search domain.
        #Grimm End
        return action

    def check_with_postalcode(self, line, zip):
        '''
        This method will check if this product is in customer delivery address postalcode or not based on
        configuration in product.postalcode configuration.
        :param line:
        :param zip:
        :return:
        '''
        product_postalcode = self.env["product.postalcode"].search([])
        for postalcode in product_postalcode:
            if postalcode.action_by == 'categ':
                if line.product_id.categ_id.id == postalcode.product_categ_id.id:
                    if zip in [postal.name for postal in postalcode.postalcode_ids]:
                        #self.env.user.notify_info(_('Route has been changed for <br/><b>%s</b>' % line.product_id.name), False)
                        line.route_id = False
            else:
                if line.product_id.id in postalcode.product_ids.ids:
                    if zip in [postal.name for postal in postalcode.postalcode_ids]:
                        #self.env.user.notify_info(_('Route has been changed for <br/><b>%s</b>' % line.product_id.name), False)
                        line.route_id = False

    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        for line in res.order_line:
            res.check_with_postalcode(line, res.partner_shipping_id.zip)
        return res

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    unit_value = fields.Monetary('Value', compute='_compute_unit_value', groups='stock.group_stock_manager')

    @api.depends('company_id', 'location_id', 'owner_id', 'product_id', 'quantity')
    def _compute_unit_value(self):
        self.unit_value = 0
        for quant in self:
            quant.unit_value = quant.value / quant.quantity

    @api.model
    def _update_available_quantity(self, product_id, location_id, quantity, lot_id=None, package_id=None, owner_id=None, in_date=None):
        """ Increase or decrease `reserved_quantity` of a set of quants for a given set of
        product_id/location_id/lot_id/package_id/owner_id.

        :param product_id:
        :param location_id:
        :param quantity:
        :param lot_id:
        :param package_id:
        :param owner_id:
        :param datetime in_date: Should only be passed when calls to this method are done in
                                 order to move a quant. When creating a tracked quant, the
                                 current datetime will be used.
        :return: tuple (available_quantity, in_date as a datetime)
        """
        self = self.sudo()
        quants = self._gather(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=True)
        rounding = product_id.uom_id.rounding

        incoming_dates = [d for d in quants.mapped('in_date') if d]
        incoming_dates = [fields.Datetime.from_string(incoming_date) for incoming_date in incoming_dates]
        if in_date:
            incoming_dates += [in_date]
        # If multiple incoming dates are available for a given lot_id/package_id/owner_id, we
        # consider only the oldest one as being relevant.
        if incoming_dates and not location_id.usage in ['supplier']:
            in_date = fields.Datetime.to_string(min(incoming_dates))
        else:
            in_date = fields.Datetime.now()

        for quant in quants:
            try:
                with self._cr.savepoint():
                    self._cr.execute("SELECT 1 FROM stock_quant WHERE id = %s FOR UPDATE NOWAIT", [quant.id], log_exceptions=False)
                    quant.write({
                        'quantity': quant.quantity + quantity,
                        'in_date': in_date,
                    })
                    # cleanup empty quants
                    if float_is_zero(quant.quantity, precision_rounding=rounding) and float_is_zero(quant.reserved_quantity, precision_rounding=rounding):
                        quant.unlink()
                    break
            except OperationalError as e:
                if e.pgcode == '55P03':  # could not obtain the lock
                    continue
                else:
                    raise
        else:
            self.create({
                'product_id': product_id.id,
                'location_id': location_id.id,
                'quantity': quantity,
                'lot_id': lot_id and lot_id.id,
                'package_id': package_id and package_id.id,
                'owner_id': owner_id and owner_id.id,
                'in_date': in_date,
            })
        return self._get_available_quantity(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=False, allow_negative=True), fields.Datetime.from_string(in_date)