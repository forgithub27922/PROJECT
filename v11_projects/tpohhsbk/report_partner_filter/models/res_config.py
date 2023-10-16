# -*- coding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2017 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import fields, api, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    partner_ledger_hide_columns = fields.Boolean(
        'Hide Columns(Account, Matching Number)')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            partner_ledger_hide_columns=self.env['ir.config_parameter'].sudo().get_param('partner_ledger_hide_columns')
        )
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('partner_ledger_hide_columns', self.partner_ledger_hide_columns)
