# -*- coding: utf-8 -*-

from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    """
    @api.onchange('invoice_line_ids')
    def _onchange_invoice_line_ids(self):
        for invoice in self:
            for line in invoice.invoice_line_ids:
                print('--------- line', line)
                if not line.analytic_account_id:
                    raise ValidationError('El campo cuenta analitica es obligatorio')
    @api.model_create_multi
    def create(self, vals_list):
        print('------------- vals_list', vals_list)
        res = super(AccountMove, self).create(vals_list)
        return res
    """

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.depends('product_id', 'account_id', 'partner_id', 'date')
    def _compute_analytic_account_id(self):
        analytic_account_id = self.env.user.account_analytic_id
        res = super(AccountMoveLine, self)._compute_analytic_account_id()
        for rec in self:
            if self.env.user.account_analytic_id:
                rec.analytic_account_id = self.env.user.account_analytic_id
        return res

    @api.model_create_multi
    def create(self, vals_list):
        res = super(AccountMoveLine, self).create(vals_list)
        for record in res:
            if not record.exclude_from_invoice_tab or not record.move_id.is_invoice(include_receipts=True):
                if (record.product_id and record.account_id and record.partner_id and record.date and not record.analytic_account_id):
                    raise ValidationError('El campo cuenta analitica es obligatorio')
        return res

    def write(self, vals):
        res = super(AccountMoveLine, self).write(vals)
        for record in self:
            if not record.exclude_from_invoice_tab or not record.move_id.is_invoice(include_receipts=True):
                if (record.product_id and record.account_id and record.partner_id and record.date and not record.analytic_account_id):
                    raise ValidationError('El campo cuenta analitica es obligatorio')
        return res

