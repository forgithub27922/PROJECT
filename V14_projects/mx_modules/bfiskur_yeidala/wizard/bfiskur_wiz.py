# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import pprint

from io import BytesIO

from odoo import api, fields, models, _
import logging
_logger = logging.getLogger(__name__)


class bfiskur_wiz(models.TransientModel):
    _name = "bfiskur.wiz"
    _description = 'wizard Action BFiskur'

    name = fields.Char(string='Name', default="")
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, default=lambda self: self.env.company)
    action_cfdiemitidos = field_name = fields.Boolean(string='Facturas Emitidos')
    action_pagosemitidos = field_name = fields.Boolean(string='Pagos Emitidos')
    action_cfdirecibidos = field_name = fields.Boolean(string='Facturas Recibidos')
    action_pagosrecibidos = field_name = fields.Boolean(string='Pagos Recibidos')
    date_start = fields.Date(string='Date Start', required=True, default=fields.Date.context_today)
    date_end = fields.Date(string='Date End', required=True, default=fields.Date.context_today)

    def action_api_bfiskur(self):
        invModel = self.env['account.move']
        if self.action_cfdiemitidos:
            invModel.action_bfiskur_setdata(self.company_id.id, 'cfdiemitidos', self.date_start, self.date_end)
        if self.action_pagosemitidos:
            invModel.action_bfiskur_setdata(self.company_id.id, 'pagosemitidos', self.date_start, self.date_end)
        if self.action_cfdirecibidos:
            invModel.action_bfiskur_setdata(self.company_id.id, 'cfdirecibidos', self.date_start, self.date_end)
        if self.action_pagosrecibidos:
            invModel.action_bfiskur_setdata(self.company_id.id, 'pagosrecibidos', self.date_start, self.date_end)