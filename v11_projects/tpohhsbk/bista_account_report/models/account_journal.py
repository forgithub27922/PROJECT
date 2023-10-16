# -*- coding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2018 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class account_journal(models.Model):
    _inherit='account.journal'

    is_overdraft = fields.Boolean(string="Overdraft Facility",copy=False)
    overdraft_limit = fields.Float(string="Overdraft Limit",copy=False,
        help="Set Overdraft Limit Amount based on Bank Journal Currency.")

    @api.constrains('is_overdraft','overdraft_limit')
    def check_overdraft_limit(self):
        for bank in self:
            if bank.is_overdraft and bank.overdraft_limit <=0:
                raise ValidationError(_('Please enter proper amount for overdraft limit.'))


class account_account(models.Model):
    _inherit='account.account'

    is_retained_earning = fields.Boolean(string="Is Retained Earning",copy=False)
