# -*- coding: utf-8 -*-

import time
from odoo import api, models
from dateutil.parser import parse
from odoo.exceptions import UserError
from datetime import datetime

class PrintTransportScheduleReport(models.AbstractModel):
    _name = 'report.sms_transport.report_transport_schedule_template'
 
    @api.model
    def _get_report_values(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        rec = self.env[self.model].browse(self.env.context.get('active_id'))
       # FOR THE TIME BEING I HAVE USE THIS WILL USE DATETIME LIBRARY LATER ibrahim 
        year = str(datetime.strptime(str(rec.schedule_date), '%Y-%m-%d').strftime('%Y'))
        month = str(datetime.strptime(str(rec.schedule_date), '%Y-%m-%d').strftime('%m'))
        day = str(datetime.strptime(str(rec.schedule_date), '%Y-%m-%d').strftime('%d'))
        date = str(day)+'-'+str(month)+'-'+str(year)
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day = datetime.strptime(date, '%d-%m-%Y').weekday()
        search_days = ["daily", days[day].lower()]
        docs =  self.env['transport.scheduling'].search([('schedule_days.code', 'in', search_days),('bus_id', 'in', rec.bus_ids.ids)])
        
        return {
            'doc_model': 'sms_transport.transport.scheduling',
            'docs': docs,
            'day':days[day]
            }
        