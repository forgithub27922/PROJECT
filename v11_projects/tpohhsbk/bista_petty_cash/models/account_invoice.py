
# -*- encoding: utf-8 -*-
#
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
#
from odoo import api, fields, models, _

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    pettycash_id = fields.Many2one('voucher.petty.cash', string="Pettycash ID")