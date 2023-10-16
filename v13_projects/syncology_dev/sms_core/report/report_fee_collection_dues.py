# -*- coding: utf-8 -*-

import time
from odoo import api, models
from dateutil.parser import parse
from odoo.exceptions import UserError
from datetime import datetime
from odoo import api, fields, models, _

        
class SelectedEmployeeAttendance(models.AbstractModel):
    _name = 'report.sms_core.fee_collection_dues_report_templet'
    
    @api.model
    def _get_report_values(self, docids, data=None):
        result = None
        self.model = self.env.context.get('active_model')
        rec = self.env[self.model].browse(self.env.context.get('active_id'))
        form = data['form']
        if form['student_id']:
            student_ids = rec.student_id.ids
        else:
            #include withdrawan or cancel students
            student_ids = self.env['academic.student'].search([]).ids
        
        print("this is student ids +++++ ",student_ids)
        date_from = form['date_from']
        date_to = form['date_to']
        status = form['filter_status']
        
        if status:
            if status in ('unpaid','paid', 'refunded'):
                stat = [status]
            else:
                stat = ['unpaid','paid', 'refunded']
        
        result = self.env['student.fee'].student_fee_reports_cm(date_from,date_to,student_ids,stat) 
        print("student fee res",result)
        return {
            'doc_ids': self.ids,
            'doc_model': 'sms_core.student.fee',
            'docs': result,
            'rec': rec,
            'date_from':date_from,
            'date_to':date_to,
#             'student_id': form['student_id'],
            #'get_attendances_recordes':self._get_attendace_records,
            #'get_remaining_leaves':self._get_remaining_casual_leaves,
        }
        