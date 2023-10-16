 # -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime


class AdmissionlistWizard(models.TransientModel):
 
    _name = "admission.list.wizard"
    _description = "Admission list wizard"
    
    date_from = fields.Date('Date from', required=True)
    date_to = fields.Date('Date to', default=datetime.today(), required=True)
    state = fields.Selection([('all','All'),('in_review','In Review'),('interview', 'Interview'),('documentation','Documentation'),('payment','Payment'), ('rejected', 'Rejected'), ('cancelled', 'Cancelled'),('admitted','Admitted')],'State',default='all')
#     report_type = fields.Selection([('admission_list', 'Admission List'), ('admission_statistics', 'Admission Statistics'), ('student_withdraw', 'Student Withdraw')], 'Report Type')
    
    def check_report(self):
        #if self.report_type == 'admission_list':
        data = {}
        data['form'] = self.read([ 'date_from', 'date_to', 'state'])[0]
        return self.env.ref('sms_core.action_report_admission_list').report_action(self, data=data, config=False)
        

