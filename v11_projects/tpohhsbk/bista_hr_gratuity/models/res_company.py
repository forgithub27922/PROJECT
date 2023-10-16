# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import fields, api, models, _


class ResCompany(models.Model):
    _inherit = "res.company"

    gratuity_journal_id = fields.Many2one('account.journal', 'Gratuity Journal')
    gratuity_account_id = fields.Many2one('account.account', 'Gratuity Expense Account')