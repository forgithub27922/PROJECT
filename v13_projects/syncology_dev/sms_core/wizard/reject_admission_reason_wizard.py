# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from odoo.tools.mail import append_content_to_html


class AdmitStudentInSchool(models.TransientModel):
 
    _name = 'admission.reject.reason.wizard'
    _description = 'admission.reject.reason.wizard'
    
    admission_id = fields.Many2one('student.admission.form')
    adm_reject_reason = fields.Text('Reason')

    def reject_student_admission(self):

        adm_id = self.env.context.get('admission_id', False)
        adm_form = self.env['student.admission.form'].browse(adm_id)
        self.write({'admission_id':adm_form.id})
        try:
            sendingData = []
            recipientData = []
            today = datetime.now()
            current_month = today.strftime("%m")
            current_year = today.strftime("%Y")
            if adm_form.state in ('in_review', 'interview', 'documentation', 'payment'):
                info = {
                    "name": adm_form['full_name'] if adm_form['full_name'] else '',
                    "reason": self.adm_reject_reason if self.adm_reject_reason else '',
                }
                sendingData.append(info)
            if len(sendingData) > 0:
                if adm_form.father_email:
                    recipientData.append(adm_form.father_email)
                if adm_form.mother_email:
                    recipientData.append(adm_form.mother_email)
                if adm_form.legal_guardian != 'father_is_legal_guardian':
                    if adm_form.guardian_email:
                        recipientData.append(adm_form.guardian_email)
#             managers = self.env['res.users'].search([('groups_id', '=', 'Employees / Manager'), ('active', '=', True)])
#             recipientData = [str(i.email) for i in managers if type(i.email) is not bool]
            if len(sendingData) > 0:
                adm_form.state = 'rejected'
                adm_form.date_of_reject_cancel = datetime.now()
                adm_form.rejected_by = self._uid
                template = self.env.ref('sms_core.reject_admission_reason_email')
                email_value = {'email_to': ','.join(recipientData), 'email_from': self.env.user.email or '',
                               'subject': 'Admission: Admission Email '}
                template.sudo().send_mail(self.id, email_values=email_value, force_send=True)
            
        except Exception as e:
            raise ValidationError(e)

        return
    
    
    @api.onchange('school_id')
    def onchange_domain(self):
        self.class_grade_id = ''
        self.class_course_ids = None
        ids_list_class_grade =[]
        for f in  self.school_id.school_class_ids:
            ids_list_class_grade.append(f.id)
        return {'domain': {'class_grade_id': [('id', 'in', ids_list_class_grade)]}}
    
    @api.onchange('class_grade_id')
    def class_onchange_domain(self):
        self.class_course_ids = None
        class_course_ids_list =[]
        course_list = self.env['class.course'].search([('class_id','=',self.class_grade_id.id),('active','=',True)])
        for f in course_list:
            class_course_ids_list.append(f.id)
        self.class_course_ids = class_course_ids_list
        return
    
    
