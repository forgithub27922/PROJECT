 # -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime


class AdmissionlistWizard(models.TransientModel):
 
    _name = "student.reports.wizard"
    _description = "student.reports.wizard"
    
    report_type = fields.Selection([('student_detail_report','Students detail'),('parents_detail_report','Parents detail')],'Report Type', required=True)
    filter = fields.Boolean('Filter')
    school_id = fields.Many2one('schools.list',string="School")
    class_id = fields.Many2one('school.class',string="Class")
    
        
    def check_report(self):
        data = {}
        data['form'] = self.read([ 'report_type', 'filter', 'school_id', 'class_id'])[0]

        if self.report_type == 'student_detail_report':
            return self.env.ref('sms_core.action_report_student_info_list').report_action(self, data=data, config=False)
        
        elif self.report_type == 'parents_detail_report':
            return self.env.ref('sms_core.action_report_parent_guardian_info').report_action(self, data=data, config=False)

