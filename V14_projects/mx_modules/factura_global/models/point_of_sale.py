# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning

class pos_order(models.Model):
    _inherit = "pos.order"

    f_global_id=fields.Many2one('account.move', string='Factura Global')

class PosSession(models.Model):
    _inherit = 'pos.session'


    def _create_account_move(self):
       # Disable account_moves on closing session
       return {}


class PosPaymentMethod(models.Model):
    _inherit = "pos.payment.method"

    l10n_mx_edi_payment_method_id = fields.Many2one(
        'l10n_mx_edi.payment.method',
        string='Payment Method on CFDI')

class PosPayment(models.Model):
    _inherit = "pos.payment"

    account_move = fields.Many2one(related='pos_order_id.account_move', string="Order Invoice")


