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
from odoo.exceptions import UserError, AccessError
import json
import logging

_logger = logging.getLogger(__name__)
class MassOperationWizardMixin(models.AbstractModel):
    _inherit = "mass.operation.wizard.mixin"

    @api.model
    def _get_remaining_items(self):
        active_ids = self.env.context.get("active_ids", [])
        mass_operation = self._get_mass_operation()
        SrcModel = self.env[mass_operation.model_id.model]
        if mass_operation.domain != "[]":
            domain = expression.AND(
                [safe_eval(mass_operation.domain), [("id", "in", active_ids)]]
            )
        else:
            domain = [("id", "in", active_ids)]
        # GRIMM START
        domain.extend(self.env.context.get("active_domain", []))
        # GRIMM END
        return SrcModel.search(domain)

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    is_so_rfq = fields.Boolean(string="Is SO RFQ?", default=False)

    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):
        super(PurchaseOrderLine, self)._onchange_quantity()
        if not self.product_id:
            return
        grimm_purchase_price = self.product_id.calculated_standard_price
        if grimm_purchase_price:
            self.price_unit = grimm_purchase_price

    @api.depends('product_uom', 'product_qty', 'product_id.uom_id')
    def _compute_product_uom_qty(self):
        super(PurchaseOrderLine, self)._compute_product_uom_qty()
        for line in self:
            if line.product_id:
                grimm_purchase_price = line.product_id.calculated_standard_price
                if grimm_purchase_price:
                    line.price_unit = grimm_purchase_price

    @api.model
    def create(self, vals):
        '''
        Override this method to set Analytic Account. (OD-741)
        :param vals:
        :return:
        '''
        res = super(PurchaseOrderLine, self).create(vals)
        if res.sale_line_id and res.sale_line_id.order_id.analytic_account_id:
            res.account_analytic_id = res.sale_line_id.order_id.analytic_account_id.id
        return res

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    is_so_rfq = fields.Boolean(string="Is SO RFQ?", default=False)
    base_so_number = fields.Char(string="Base SO Number", default=False)
    so_team_id = fields.Many2one("crm.team", string='SO Team', related='sale_order_id.team_id', store=True, readonly=True)
    so_analytic_account_id = fields.Many2one("account.analytic.account", related='sale_order_id.analytic_account_id', store=True, string='SO Analytic Account',readonly=True)
    po_review_state = fields.Selection(
        selection=[('new', 'New'),
                   ('ready', 'Ready for Exam'),
                   ('deman', 'Demand'),
                   ('finish', 'Finish'),
                   ('cancel', 'Cancel'),
                   ],
        string='Review State',
        default="new",
        group_expand = '_read_group_state',
        help="This will help to review Purchase order's attachment created from mail.",
    )
    created_since = fields.Integer("Created since (hours)", compute="_po_created_since")

    def _po_created_since(self):
        self.created_since = 0
        for po in self:
            current_time = fields.Datetime.now()
            created_time = po.create_date
            diff = current_time - created_time
            days, seconds = diff.days, diff.seconds
            po.created_since = days * 24 + seconds // 3600



    @api.model
    def _read_group_state(self, stages, domain, order):
        # retrieve job_id from the context and write the domain: ids + contextual columns (job or default)
        temp_list = [key for key, val in type(self).po_review_state.selection]
        temp_list.remove('cancel')
        return temp_list

    def button_confirm(self):
        if self.base_so_number and self.sale_order_id and self.sale_order_id.state in ['draft', 'sent']:
            raise UserError(_('Please confirm related Sale Order before Purchase Order confirmation.'))
        result = super(PurchaseOrder, self).button_confirm()
        # self.write({'po_review_state': 'finish'})
        return result

    def button_cancel(self):
        result = super(PurchaseOrder, self).button_cancel()
        self.write({'po_review_state': 'cancel'})
        return result