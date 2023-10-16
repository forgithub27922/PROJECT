# -*- coding: utf-8 -*-

import time
from odoo import api, models
from dateutil.parser import parse
from odoo.exceptions import UserError
from datetime import datetime

class PrintStdBiodataReport(models.AbstractModel):
    _name = 'report.sms_core.report_std_adm_biodata_template'


    @api.model
    def _get_report_values(self, docids, data=None):
#         data = {}
#         data['form'] = self.read(['id','state'])[0]
#         return self.env.ref('sms_core.action_std_admission_biodata_report').report_action(self, data=data, config=False)
    
        self.model = self.env.context.get('active_model')
        print("self model is ==== ",self.model)
        act_id = self.env[self.model].browse(self.env.context.get('active_id'))
        print("self model id is ==== ",act_id)
        std_rec = self.env['student.admission.form'].search([('id', '=', act_id.id)],limit =10)
        return {
            'o': docids,
            'doc_model': 'student.admission.form',
            'docs': std_rec,
            'data': data,
            
        }
        
