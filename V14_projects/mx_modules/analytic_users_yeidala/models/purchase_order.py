# -*- coding: utf-8 -*-

from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.depends('picking_type_id')
    def _compute_analytic_id_and_tag_ids(self):
        for rec in self:
            rec.user_account_analytic_ids = []  

    user_account_analytic_ids = fields.Many2many('account.analytic.account', string='Analytic Accounts', compute='_compute_analytic_id_and_tag_ids')

    @api.model
    def _get_picking_type(self, company_id):
        res = super(PurchaseOrder, self)._get_picking_type(company_id=company_id)
        account_analytic_id = self.env.user.account_analytic_id
        if account_analytic_id:
            picking_type = self.env['stock.picking.type'].search([('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id), ('warehouse_id.account_analytic_id', '=', self.env.user.account_analytic_id.id)])
            if picking_type:
                return picking_type[:1]
        return False

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.depends('product_id', 'date_order')
    def _compute_account_analytic_id(self):
        res = super(PurchaseOrderLine, self)._compute_account_analytic_id()
        for rec in self:
            rec.account_analytic_id = self.env.user.account_analytic_id

