# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, SUPERUSER_ID, _

class Company(models.Model):
    _inherit = "res.company"

    internal_journal_id = fields.Many2one(
        'account.journal', 'Internal Journal', ondelete="restrict", check_company=True,
        help="Technical field used for resupply routes between warehouses that belong to this company")

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    internal_journal_id = fields.Many2one(related='company_id.internal_journal_id', readonly=False)



