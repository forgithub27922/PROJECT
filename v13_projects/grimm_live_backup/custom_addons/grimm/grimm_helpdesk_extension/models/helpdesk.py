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
from odoo.exceptions import ValidationError, MissingError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    ticket_id = fields.Many2one("helpdesk.ticket",string="Helpdesk Ticket")
    helpdesk_ticket_count = fields.Integer(compute='_compute_helpdesk_ticket_count', string='Helpdesk Tickets')

    def get_helpdesk_ticket_count(self):
        ticket_id_list = []
        helpdesks = self.env['helpdesk.ticket'].search([('order_number', 'in', [self.name])])
        for hd in helpdesks:
            ticket_id_list.extend(hd.ids)
        return ticket_id_list

    def _compute_helpdesk_ticket_count(self):
        self.helpdesk_ticket_count = 0
        for so in self:
            all_tickets = so.get_helpdesk_ticket_count()
            so.helpdesk_ticket_count = len(all_tickets)


    def get_helpdesk_ticket(self):
        id_list = self.get_helpdesk_ticket_count()
        if id_list:
            return {
                'name': _('Related Ticket'),
                'domain': [('id', 'in', id_list)],
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'helpdesk.ticket',
                'view_id': False,
                'type': 'ir.actions.act_window',
            }


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    def _default_partner_id(self):
        return self.env.user.partner_id.id

    def _get_claim_count(self):
        self.claim_count = 0
        for rec in self:
            rec.claim_count = self.env['crm.claim'].search_count([('ticket_id', '=', rec.id)])

    claim_count = fields.Integer("Claim count", compute="_get_claim_count")


    sale_ids = fields.One2many('sale.order','ticket_id', string='Sale Orders')
    sale_order_count = fields.Integer(compute='_compute_sale_order_count', string='# of Sales Order')
    supplier_invoice_count = fields.Integer(compute='_compute_supplier_invoice_count', string='Supplier Invoice')
    related_invoice_ids = fields.Many2many('account.move',compute='_compute_related_invoice', string="Related Supplier Bill", help="This invoice is possible invoice based on provided information by customer like Invoice Number, Order Number.")

    role_partner = fields.Many2one('crm.claim.role_partner', string="Rollenpartner")
    brand_id = fields.Many2one('res.partner', string="Brand Partner")
    brand_phone = fields.Char(related='brand_id.phone', store=True)
    brand_mobile = fields.Char(related='brand_id.mobile', store=True)
    brand_email = fields.Char(related='brand_id.email', store=True)

    #fsm_order_id = fields.Many2one('fsm.order', string="FSM Order")
    product_description = fields.Text(string="Product Description")
    invoice_number = fields.Char(string="Invoice Number")
    invoice_date = fields.Date(string="Invoice Date")
    serial_number = fields.Char(string="Serial Number")
    order_number = fields.Char(string="Order Number")
    parts_info = fields.Char(string="Spare Parts Info")
    is_maintenance = fields.Boolean(string="Is Maintenance ?")
    manufacturer = fields.Char(string="Manufacturer")
    product_type = fields.Char(string="Product Type")
    product_model = fields.Char(string="Product Model")
    construction_year = fields.Char(string="Year of Construction")
    comments = fields.Text(string="Comments")
    partner_id = fields.Many2one('res.partner', string='Customer',default=_default_partner_id)
    reason = fields.Char(string="Reason")
    grimm_customer_number = fields.Char(string="Grimm Customer Number")

    @api.onchange('brand_id')
    def _onchange_brand_id(self):
        if self.brand_id:
            if self.brand_id.phone:
                self.brand_phone = self.brand_id.phone
            if self.brand_id.mobile:
                self.brand_mobile = self.brand_id.mobile
            if self.brand_id.email:
                self.brand_email = self.brand_id.email

    def _compute_sale_order_count(self):
        all_orders = self.env["sale.order"].search([('ticket_id', '=', self.id)])
        self.sale_order_count = len(all_orders)

    def _compute_related_invoice(self):
        self.related_invoice_ids = [(6, 0, [])]
        if self.invoice_number:
            cust_invoice_number = self.env['account.move'].search([('name', '=', self.invoice_number)])
            purchase_orders = self.env['purchase.order'].search([('origin', 'in', [order.name for order in self.env["sale.order"].search([('partner_id', '=', self.partner_id.id),('name', '=', cust_invoice_number.invoice_origin)])])])
            invoice_list = []
            for po in purchase_orders:
                invoice_list.extend(po.invoice_ids.ids)
            if invoice_list:
                self.related_invoice_ids = [(6, 0, invoice_list)]
        if self.order_number:
            purchase_orders = self.env['purchase.order'].search([('origin', 'in', [order.name for order in self.env["sale.order"].search([('partner_id', '=', self.partner_id.id), ('name', '=', self.order_number)])])])
            invoice_list = []
            for po in purchase_orders:
                invoice_list.extend(po.invoice_ids.ids)
            if invoice_list:
                self.related_invoice_ids = [(6, 0, invoice_list)]

    def get_supplier_invoice_count(self):
        invoice_id_list = []
        purchase_orders = self.env['purchase.order'].search([('origin', 'in', [order.name for order in self.env["sale.order"].search([('partner_id', '=', self.partner_id.id)])])])
        for po in purchase_orders:
            invoice_id_list.extend(po.invoice_ids.ids)
        return invoice_id_list

    def get_supplier_invoice(self):
        invoice_id_list = self.get_supplier_invoice_count()
        if invoice_id_list:
            return {
                'name': _('Related Supplier Invoices'),
                'domain': [('id', 'in', invoice_id_list)],
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.move',
                'view_id': False,
                'type': 'ir.actions.act_window',
            }

    def _compute_supplier_invoice_count(self):
        all_invoices = self.get_supplier_invoice_count()
        self.supplier_invoice_count = len(all_invoices)

    def open_detail_view(self):
        invoice_id_list = self.related_invoice_ids.ids
        if invoice_id_list:
            return {
                'name': _('Related Supplier Invoices'),
                'domain': [('id', 'in', invoice_id_list)],
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.move',
                'view_id': False,
                'type': 'ir.actions.act_window',
            }

    @api.model
    def create(self, vals):
        if "rating-noreply@trustedshops.de" not in str(vals.get("partner_email", "")):
            return super(HelpdeskTicket, self).create(vals)
        else:
            raise ValidationError(_('Record cannot be created for rating-noreply@trustedshops.de'))

    def action_view_crm_claim(self):
        action = self.env.ref('grimm_helpdesk_extension.act_helpdesk_crm_claim').read()[0]
        action['domain'] = [('ticket_id', 'in', self.ids)]
        priority = self.priority
        if int(priority) > 2:
            priority = '2'
        ctx = {
            'default_ticket_id':self.id,
            'default_partner_id': self.partner_id.id,
            'default_name': self.description,
            'default_priority': priority,
            'default_serial_number': self.serial_number,
        }
        if self.invoice_number:
            invoice_number = self.env['account.move'].search([('name', '=', self.invoice_number)],limit=1)
            if invoice_number:
                ctx["default_inv_id"] = invoice_number.id
        if self.manufacturer:
            manufacturer = self.env['grimm.product.brand'].search([('name', '=', self.manufacturer)],limit=1)
            if manufacturer:
                ctx["default_manufacturer_id"] = manufacturer.id
        if self.reason:
            reason = self.env['crm.claim.category'].search([('name', '=', self.reason)],limit=1)
            if reason:
                ctx["default_categ_id"] = reason.id
        action['context'] = ctx
        return action

    def open_related_invoice(self):
        self.ensure_one()
        invoice = self.env['account.move'].search([('name', '=', self.invoice_number)], limit=1)
        if invoice and self.invoice_number:
            return {
                'name': _('Invoice'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.move',
                'res_id': invoice.id,
                'type': 'ir.actions.act_window',
                'target': 'self',
            }
        else:
            raise MissingError('Invoice is not available in the system.')

    def open_related_order(self):
        self.ensure_one()
        order = self.env['sale.order'].search([('name', '=', self.order_number)], limit=1)
        if order and self.order_number:
            return {
                'name': _('Order'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sale.order',
                'res_id': order.id,
                'type': 'ir.actions.act_window',
                'target': 'self',
            }
        else:
            raise MissingError('Order is not available in the system.')