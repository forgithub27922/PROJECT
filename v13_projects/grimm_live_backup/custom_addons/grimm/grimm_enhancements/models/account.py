# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    purchase_id_copy = fields.Many2one(
        comodel_name='purchase.order',
        string='Source Document',
        readonly=True, states={'draft': [('readonly', False)]},
        compute='_compute_po'
    )

    @api.depends('invoice_origin')
    def _compute_po(self):
        for rec in self:
            rec.purchase_id_copy = self.env['purchase.order'].search([('name', '=', rec.invoice_origin)])
