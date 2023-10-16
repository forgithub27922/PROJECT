# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################


from odoo import fields, models, api, _
from odoo.exceptions import Warning


class wizrad_print_check(models.Model):
    _name ='wizard.print.check'

    name = fields.Char(string="Name")
    date = fields.Date(string="Date")
    partner_id = fields.Many2one('res.partner',string="Partner")
    company_id = fields.Many2one('res.company',string="Company",default=lambda self: self.env.user.company_id)
    amount = fields.Float(string="Amount")
    check_format_id = fields.Many2one('cheque.format', string="Cheque Format")
    amount_in_words = fields.Char(compute='_get_amount_in_words',string="Amount In Words")
    description = fields.Text(string="Description")

    @api.multi
    def print_check_report(self):
        if self.amount <=0:
            raise Warning(_('Please enter proper amount.'))
        return self.env.ref('check_uae_print.action_custom_print_check').report_action(self)

    @api.depends('amount')
    def _get_amount_in_words(self):
        for record in self:
            record.amount_in_words= record.company_id.currency_id.amount_to_text(record.amount)
