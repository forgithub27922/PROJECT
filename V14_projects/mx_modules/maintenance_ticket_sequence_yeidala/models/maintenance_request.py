# -*- coding: utf-8 -*-

import ast

from datetime import date, datetime, timedelta

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    ticket = fields.Char(string='Number of Ticket', copy=False, readonly=False, index=True, default=lambda self: _('New'))

    @api.model
    def create(self, vals):
        if vals.get('ticket', _('New')) == _('New'):
            vals['ticket'] = self.env['ir.sequence'].next_by_code('maintenance.request', sequence_date=fields.Date.context_today(self)) or _('New')
        result = super(MaintenanceRequest, self).create(vals)
        return result

    def create_seq_index(self):
        ticket_ids = self.search([('ticket', '=',  _('New'))])
        for ticket_id in ticket_ids:
            year = ticket_id.request_date.year
            ids = '%s'%( str(ticket_id.id).rjust(5, '0') )
            ticket_name = 'PM/%s/%s'%( year, ids )
            ticket_id.ticket = ticket_name

