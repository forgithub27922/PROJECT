# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from odoo import api, fields, models, tools, SUPERUSER_ID

class ResCompany(models.Model):
    _inherit = 'res.company'

    bfiskur_active_api = fields.Boolean(
        string='BFiskur Active API',
        help='Enable the usage of api credentials',
        default=False)
    bfiskur_url = fields.Char(
        string='BFiskur URL',
        help='The username used to send the CSV file to bfiskur', 
        default="https://kpionline5.bitam.com/artus/gen903/xls_loader_bfiskur/loadservice.php")
    bfiskur_username = fields.Char(
        string='BFiskur username',
        help='The username used to send the CSV file to bfiskur', default="plogapi@bFiskur.com")
    bfiskur_password = fields.Char(
        string='BFiskur password',
        help='The password used to send the CSV file to bfiskur', default="2938")



    def _load_bfiskur_api(self):
        invModel = self.env['account.move']
        today = fields.Date.context_today(self)
        yesterday = fields.Date.context_today(self) + timedelta(days=-10)
        datas = {}
        for cia_id in self.sudo().search([('bfiskur_active_api', '=', True)]):
            # CFDI Emitidos

            # datas['cfdiemitidos'] = invModel.action_bfiskur_setdata(cia_id, 'cfdiemitidos', yesterday, today)
            pagos_emitidos = invModel.action_bfiskur_setdata(cia_id.id, 'pagosemitidos', yesterday, today)
            print('--- pagos_emitidos', pagos_emitidos)            