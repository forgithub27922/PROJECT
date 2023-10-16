 # -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime


class TransportScheduleWizard(models.TransientModel):
 
    _name = "transport.schedule.wizard"
    _description = "Transport Schedule wizard"
    
    schedule_date = fields.Date('Date', required=True)
    bus_ids = fields.Many2many('fleet.vehicle')

    
    def check_report(self):
        data = {}
        data['form'] = self.read([ 'schedule_date', 'bus_ids'])[0]
        return self.env.ref('sms_transport.action_report_transport_schedule').report_action(self, data=data, config=False)
        

