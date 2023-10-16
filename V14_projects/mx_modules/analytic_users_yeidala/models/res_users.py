# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.addons.purchase.models.purchase import PurchaseOrder as Purchase

class Users(models.Model):
    _inherit = "res.users"

    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic Account Default')
    account_analytic_ids = fields.Many2many('account.analytic.account', string='Analytic Accounts')
