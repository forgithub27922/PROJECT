# -*- coding: utf-8 -*-

import time
from odoo import api, models
from dateutil.parser import parse
from odoo.exceptions import UserError
from datetime import datetime

class PrintAdmissionReport(models.AbstractModel):
    _name = 'report.sms_core.report_parent_guardian_info_template'
    
    @api.model
    def _get_report_values(self, docids, data=None):
    
        result = []
        self.model = self.env.context.get('active_model')
        rec = self.env[self.model].browse(self.env.context.get('active_id'))
        
        parent_ids = self.env['student.parent.guardian.info'].search([], order='id')
        result = []
        
        for p in parent_ids:
            mydict = {'g_name': '','national_id':'','login':'','child_dict':''}
            result2 = []
            for std in p.student_ids:
                child_records = {'std_name':'','national_id':'','grade':'', 'login':'', 'status':''}
                
                child_records['std_name'] = std.full_name
                child_records['national_id'] = std.national_id
                child_records['grade'] = std.class_id
                child_records['login'] = std.md_username
                child_records['status'] = std.state
                result2.append(child_records)
                
            mydict['g_name'] = p.name
            
            if p.head_person == 'father':
                mydict['national_id'] = p.father_national_id
            elif p.head_person == 'mother':
                mydict['national_id'] = p.mother_national_id
            else:
                mydict['national_id'] = p.guardian_national_id
             
            mydict['login'] = '+++++'
            mydict['child_dict'] = result2
            result.append(mydict)
            
        return {
        'doc_ids': self.ids,
        'doc_model': 'sms_core.academic.student',
        'docs': result,
#             'total_students':total_students,
    }
        