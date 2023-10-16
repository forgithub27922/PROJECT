# -*- coding: utf-8 -*-

import time
from odoo import api, models
from dateutil.parser import parse
from odoo.exceptions import UserError
from datetime import datetime

class PrintAdmissionReport(models.AbstractModel):
    _name = 'report.sms_core.report_admission_list_template'
 
    @api.model
    def _get_report_values(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        rec = self.env[self.model].browse(self.env.context.get('active_id'))
       
        if rec.state:
            if rec.state in ('in_review','interview','documentation','payment','admitted','rejected','cancelled'):
                stat = ('state', '=', rec.state)
            else:
                stat = ('state', 'in', ['in_review','interview','documentation','payment','admitted','rejected','cancelled'])
        ids = self.env['student.admission.form'].search([stat,('date_of_apply', '>=', rec.date_from),('date_of_apply', '<=', rec.date_to)])
        
        total_admissions = len(ids)
        docs = self.env['student.admission.form'].browse([ids]).id
       
        return {
            'doc_ids': self.ids,
            'doc_model': 'sms_core.student.admission.form',
            'docs': docs,
            'date_from': datetime.strptime(str(rec.date_from),'%Y-%m-%d').strftime('%d-%b-%Y'),
            'date_to': datetime.strptime(str(rec.date_to),'%Y-%m-%d').strftime('%d-%b-%Y'),
            'state':rec.state,
            'total_admissions':total_admissions,
        }
        