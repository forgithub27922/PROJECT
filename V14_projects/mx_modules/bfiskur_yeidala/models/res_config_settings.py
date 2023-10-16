# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    bfiskur_active_api = fields.Boolean(
        related='company_id.bfiskur_active_api', readonly=False,
        string='Active API *')
    bfiskur_url = fields.Char(
        related='company_id.bfiskur_url', readonly=False,
        string='URL *')
    bfiskur_username = fields.Char(
        related='company_id.bfiskur_username', readonly=False,
        string='Username *')
    bfiskur_password = fields.Char(
        related='company_id.bfiskur_password', readonly=False,
        string='Password *')

