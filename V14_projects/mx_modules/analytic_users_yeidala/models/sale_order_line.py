# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    account_analytic_id = fields.Many2one('account.analytic.account', 
        store=True, string='Analytic Account', 
        compute='_compute_analytic_id_and_tag_ids', readonly=False)

    @api.depends('product_id', 'account_analytic_id')
    def _compute_analytic_id_and_tag_ids(self):
        for rec in self:
            rec.account_analytic_id = self.env.user.account_analytic_id
