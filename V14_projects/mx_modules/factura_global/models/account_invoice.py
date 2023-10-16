# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning

class account_invoice(models.Model):
    _inherit = "account.move"

    f_global=fields.Boolean(string='Es Factura Global', readonly=True)
    pedidos_pos=fields.One2many('pos.order','account_move', readonly=True)
    payments_pos = fields.One2many('pos.payment', 'account_move', readonly=True )

    payments_pos_count = fields.Integer(string='# of Pos Payments', compute='_get_pos_payments', readonly=True)

    def action_view_payments_pos(self):
        payments = self.mapped('payments_pos')
        action = self.env.ref('point_of_sale.action_pos_payment_form').read()[0]
        if len(payments) > 1:
            action['domain'] = [('id', 'in', payments.ids)]
            action['context'] = {'group_by': 'payment_method_id'}
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action




    @api.depends('payments_pos','payments_pos.account_move')
    def _get_pos_payments(self):

       for invoice in self:
           invoice.update({
               'payments_pos_count': invoice.f_global and len(set(invoice.payments_pos.ids)) or 0,
           })


class account_tax(models.Model):
    _inherit = "account.tax"

    f_global=fields.Boolean(string='Aplica para Factura Global')



