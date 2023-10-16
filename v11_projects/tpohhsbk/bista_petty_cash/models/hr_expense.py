
# -*- encoding: utf-8 -*-
#
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
#
from odoo import api, fields, models, _

class HRExpenses(models.Model):
    _inherit = 'hr.expense'

    pettycash_id = fields.Many2one('voucher.petty.cash', string="Pettycash ID")
    pettycash_id_state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submit'),
        ('approved_manager', 'Approved by Manager'),
        ('approved_hr', 'Approved by HR'),
        ('approved_finance', 'Approved by Finance'),
        ('paid', 'Paid'),
        ('reconciled', 'Reconciled')],
        string='Status', related="pettycash_id.state")


class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    pettycash_id = fields.Many2one('voucher.petty.cash', string="Pettycash ID")