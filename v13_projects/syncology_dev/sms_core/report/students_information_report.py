# -*- coding: utf-8 -*-

import time
from odoo import api, models
from dateutil.parser import parse
from odoo.exceptions import UserError
from datetime import datetime

class PrintAdmissionReport(models.AbstractModel):
    _name = 'report.sms_core.report_student_info_list_template'
 
    @api.model
    def _get_report_values(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        rec = self.env[self.model].browse(self.env.context.get('active_id'))
       
        ids = self.env['academic.student'].search([('state', '=', 'admitted')])
        print("report ids ====== ",ids)
        total_students = len(ids)
        docs = self.env['academic.student'].browse([ids]).id
       
        return {
            'doc_ids': self.ids,
            'doc_model': 'sms_core.academic.student',
            'docs': docs,
            'total_students':total_students,
        }
        