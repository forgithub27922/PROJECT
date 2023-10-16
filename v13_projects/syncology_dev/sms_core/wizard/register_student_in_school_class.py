# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
import requests, json
from datetime import datetime, timedelta
from datetime import datetime
from datetime import date
from _ast import Try
from email.policy import default
from odoo.addons.test_convert.tests.test_env import field
from odoo.tools.mail import append_content_to_html
import string


class AdmitStudentInSchool(models.TransientModel):
 
    _name = 'admit.student.school.wizard'
    _description = 'admit.student.school.wizard'
    
    line_rec_id =fields.Many2one('student.class')
    parent_id = fields.Many2one('academic.student')
    admission_id = fields.Many2one('student.admission.form')
    school_id = fields.Many2one('schools.list',string = 'School', domain="[('active', '=', True)]")
    class_grade_id = fields.Many2one('school.class',string='Grade')
    section_id = fields.Many2one('class.section', string='Class')
    max_capacity = fields.Integer(string='Max Capacity', readonly=True)
    current_strength = fields.Integer(string='Current Strength', readonly=True)
    class_course_ids = fields.Many2many('class.course', string='Courses')
    wizard_mode = fields.Selection([('admission', 'Admission'), ('academic_student', 'Academic Student')], string='Mode',default='admission')
    religion = fields.Selection([('muslim', 'Muslim'), ('christian', 'Christian'), ('other', 'Other')],
                                default='muslim', string='Religion')
    second_language = fields.Char('Second Language')

    @api.model
    def default_get(self, field_list):
        application_for_id = False
        class_grade = False
        class_section = False
        second_language = False
        religion = False
        res = super(AdmitStudentInSchool, self).default_get(field_list)
        if self._context.get('active_id') and self._context.get('active_model'):
            if self._context.get('active_model') == 'student.admission.form':
                student = self.env[self._context.get('active_model')].browse(self._context.get('active_id'))
                application_for_id = student.application_for_id.id
                class_grade = student.class_grade.id
            if self._context.get('active_model') == 'academic.student':
                student = self.env[self._context.get('active_model')].browse(self._context.get('active_id'))
                application_for_id = student.school_id.id
                class_grade = student.class_id.id
                class_section = student.class_section_id.id
                second_language = student.second_language
                religion = student.religion
            res.update({'school_id': application_for_id or False,
                        'class_grade_id': class_grade or False,
                        'section_id': class_section or False,
                        'second_language': second_language or '',
                        'religion': religion or False,
                        })
        return res
    
    def register_student_in_school_class(self):
        parent_name = ''
        admission_id = self.env.context.get('admission_id', False)
        rec = self.env['student.admission.form'].browse(admission_id)
        rec.school_id = self.school_id.id
        rec.class_id = self.class_grade_id.id
        if not rec.father_is_absent:
            parent_name = str(rec.father_first_name or '') + ' ' + str(rec.father_middle_name or '') + ' ' + str(rec.father_last_name or '') + ' ' + str(rec.father_fourth_name or '')

        elif not rec.mother_is_absent:
            parent_name = rec.mother_first_name + ' ' + rec.mother_middle_name + ' ' + rec.mother_last_name + ' ' + rec.mother_fourth_name
        else:
            parent_name = rec.guardian_full_name + ' ' + rec.guardian_middle_name + ' ' + rec.guardian_last_name + ' ' + rec.guardian_fourth_name
        parent_name = parent_name.strip()
        parent_name_str_arr = parent_name.split(" ")
        parent_first_name = parent_name_str_arr[0]
        parent_last_name = ''
        for x in range(1, len(parent_name_str_arr)):
            parent_last_name = str(parent_last_name) + " " + str(parent_name_str_arr[x])

        std_unique_id = rec.id
        std_name = rec.first_name
        std_first_name = std_name.split()[0]
        school_domain = self.school_id.domain_name
        
        std_email_prefix = 'st.'
        parent_email_prefix = 'pr.'
        
        if std_unique_id:
            temp_seq = str(std_unique_id).zfill(5)
        std_email = str(std_email_prefix)+str(std_first_name.lower())+str(temp_seq)+"@"+str(school_domain)
        parent_email = str(parent_email_prefix)+str(parent_first_name.lower())+str(temp_seq)+"@"+str(school_domain)
        std_password = 'st_'+str(std_first_name.lower())+str(temp_seq)+'_sync'
        std_email = std_email.replace(" ", "") 
#         full_name = rec.name.split()
        first_name = rec.first_name
        last_name = str(rec.middle_name) + " " + str(rec.second_middle_name) + " " + str(rec.last_name)
        # if last_name:
            # last_name = rec.first_name
        ############CREATE STUDENT ON MOODEL###############################
        try:
            if self.env.company.synced_with_lms:
                parameters= '&users[0][username]='+str(std_email.strip())+'&users[0][firstname]='+str(first_name)+'&users[0][lastname]='+str(last_name)+'&users[0][email]='+str(std_email)+'&users[0][createpassword]=1'+'&users[0][password]='+str(std_password)+'&users[0][phone1]=0915833860'
                moodle_url = 'http://'+self.env.company.lms_url+'/webservice/rest/server.php' + '?wstoken=' + self.env.company.lms_url_token +parameters+'&wsfunction=core_user_create_users&moodlewsrestformat=json'
                head_params = {'wsfunction':'core_user_create_users', 'moodlewsrestformat':'json'}
                response = requests.get(moodle_url, params=head_params)
                response = response.json()
                if response:
                    if 'errorcode' in response:
                        print("Create Student/user on moodle", response['debuginfo'])
                    else:
                        response = response[0]
                        if 'id' in response:
                            rec.mooddle_id = response['id']
                            rec.md_password = std_password
                            rec.md_username = std_email
                            rec.md_parent_username = parent_email
                            #update password
                            parameters = '&users[0][id]=' + str(response['id']) + '&users[0][password]=' + str(std_password)
                            moodle_url = 'http://'+self.env.company.lms_url + '/webservice/rest/server.php'  + '?wstoken=' + self.env.company.lms_url_token + parameters + '&wsfunction=core_user_update_users&moodlewsrestformat=json'
                            head_params = {'wsfunction':'core_user_update_users', 'moodlewsrestformat':'json'}
                            response = requests.get(moodle_url, params=head_params)
                            response = response.json()
        except:
            raise UserError(_('Record not created on lms contact your system administrator'))
        #################### END CREATE STUDENT ON MOODEL #######################



        parent_email = parent_email.replace(" ", "")
        ############CREATE PARENT ON MOODEL##################################
        try:
            if self.env.company.synced_with_lms:
                parameters= '&users[0][username]='+str(parent_email.strip())+'&users[0][firstname]='+str(parent_first_name)+'&users[0][lastname]='+str(parent_last_name)+'&users[0][email]='+str(parent_email)+'&users[0][createpassword]=1'+'&users[0][password]='+str(std_password)+'&users[0][phone1]=0915833860'
                moodle_url ='http://'+self.env.company.lms_url + '/webservice/rest/server.php'  + '?wstoken=' + self.env.company.lms_url_token +parameters+'&wsfunction=core_user_create_users&moodlewsrestformat=json'
                head_params = {'wsfunction':'core_user_create_users', 'moodlewsrestformat':'json'}
                response = requests.get(moodle_url, params=head_params)
                response = response.json()
                if response:
                    if 'errorcode' in response:
                        print("Parent create error response",response['debuginfo'])
                    else:
                        response = response[0]
                        if 'id' in response:
    #                         rec.md_password = first_part
                            rec.md_parent_username = parent_email
        except:
            raise UserError(_('Record not created on lms contact your system administrator'))

        std_family = self.env['student.parent.guardian.info'].sudo().create({
                    #Father
                    'father_full_name': str(rec.father_first_name or "") + ' ' + str(rec.father_middle_name or "") + ' ' + str(rec.father_last_name or "") + ' ' + str(rec.father_fourth_name or ""),
                    'father_first_name': rec.father_first_name,
                    'father_middle_name': rec.father_middle_name,
                    'father_last_name': rec.father_last_name,
                    'father_fourth_name': rec.father_fourth_name,
                    'father_full_name_arabic': str(rec.father_first_name_arabic or "") + ' ' + str(rec.father_middle_name_arabic or "") + ' ' + str(rec.father_last_name_arabic or "") + ' ' + str(rec.father_fourth_name_arabic or ""),
                    'father_first_name_arabic': rec.father_first_name_arabic,
                    'father_middle_name_arabic': rec.father_middle_name_arabic,
                    'father_last_name_arabic': rec.father_last_name_arabic,
                    'father_fourth_name_arabic': rec.father_fourth_name_arabic,
                    'father_national_id': rec.father_national_id,
                    'father_passport': rec.father_passport,
                    'father_nationality': rec.father_nationality.id,
                    'father_marital_status': rec.father_marital_status,
                    'father_degree_education': rec.father_degree_education,
                    'father_employment': rec.father_employment,
                    'father_employer_location': rec.father_employer_location,
                    'father_landline_number': rec.father_landline_number,
                    'father_land_line_no': rec.father_land_line_no,
                    'father_mobile_no': rec.father_mobile_no,
                    'father_email': rec.father_email,
                    'father_is_absent': rec.father_is_absent,
                    #Mother
                     'mother_full_name': str(rec.mother_first_name or "") + ' ' + str(rec.mother_middle_name or "") + ' ' + str(rec.mother_last_name or "") + ' ' + str(rec.mother_fourth_name or ""),
                    'mother_first_name': rec.mother_first_name,
                    'mother_middle_name': rec.mother_middle_name,
                    'mother_last_name': rec.mother_last_name,
                    'mother_fourth_name': rec.mother_fourth_name,
                    'mother_full_name_arabic': str(rec.mother_first_name_arabic or "") + ' ' + str(rec.mother_middle_name_arabic or "") + ' ' + str(rec.mother_last_name_arabic or "") + ' ' + str(rec.mother_fourth_name_arabic or ""),
                    'mother_first_name_arabic': rec.mother_first_name_arabic,
                    'mother_middle_name_arabic': rec.mother_middle_name_arabic,
                    'mother_last_name_arabic': rec.mother_last_name_arabic,
                    'mother_fourth_name_arabic': rec.mother_fourth_name_arabic,
                    'mother_national_id': rec.mother_national_id,
                    'mother_passport': rec.mother_passport,
                    'mother_nationality': rec.mother_nationality.id,
                    'mother_marital_status': rec.mother_marital_status,
                    'mother_degree_education': rec.mother_degree_education,
                    'mother_employment': rec.mother_employment,
                    'mother_employer_location': rec.mother_employer_location,
                    'mother_landline_number': rec.mother_landline_number,
                    'mother_land_line_no': rec.mother_land_line_no,
                    'mother_mobile_no': rec.mother_mobile_no,
                    'mother_email': rec.mother_email,
                    'mother_is_absent': rec.mother_is_absent,
                    #Guardian
                    'legal_guardian': rec.legal_guardian,
                    'guardian_full_name': str(rec.guardian_first_name or "") + ' ' + str(rec.guardian_middle_name or "") + ' ' + str(rec.guardian_last_name or "") + ' ' + str(rec.guardian_fourth_name or ""),
                    'guardian_first_name': rec.guardian_first_name,
                    'guardian_middle_name': rec.guardian_middle_name,
                    'guardian_last_name': rec.guardian_last_name,
                    'guardian_fourth_name': rec.guardian_fourth_name,
                    'guardian_full_name_arabic': str(rec.guardian_first_name_arabic or "") + ' ' + str(rec.guardian_middle_name_arabic or "") + ' ' + str(rec.guardian_last_name_arabic or "") + ' ' + str(rec.guardian_fourth_name_arabic or ""),
                    'guardian_first_name_arabic': rec.guardian_first_name_arabic,
                    'guardian_middle_name_arabic': rec.guardian_middle_name_arabic,
                    'guardian_last_name_arabic': rec.guardian_last_name_arabic,
                    'guardian_fourth_name_arabic': rec.guardian_fourth_name_arabic,
                    'guardian_national_id': rec.guardian_national_id,
                    'guardian_passport': rec.guardian_passport,
                    'guardian_nationality': rec.guardian_nationality.id,
                    'guardian_marital_status':rec.guardian_marital_status,
                    'relation_to_child': rec.relation_to_child,
                    'guardian_degree_education': rec.guardian_degree_education,
                    'guardian_employment': rec.guardian_employment,
                    'guardian_employeer_location': rec.guardian_employeer_location,
                    'guardian_landline_number': rec.guardian_landline_number,
                    'guardian_land_line_no': rec.guardian_land_line_no,
                    'guardian_mobile_no': rec.guardian_mobile_no,
                    'guardian_email': rec.guardian_email,
                    
                    })
        
        std_id = self.env['academic.student'].sudo().create({
                    'student_image': rec.student_image,
                    'full_name': str(rec.first_name) + " " + str(rec.middle_name) + " " + str(rec.second_middle_name) + " " + str(rec.last_name),
                    'first_name': rec.first_name,
                    'middle_name': rec.middle_name,
                    'second_middle_name': rec.second_middle_name,
                    'last_name': rec.last_name,
                    'first_name_arabic': rec.first_name_arabic,
                    'middle_name_arabic': rec.middle_name_arabic,
                    'second_middle_name_arabic': rec.second_middle_name_arabic,
                    'last_name_arabic': rec.last_name_arabic,
                    'full_name_arabic': str(rec.first_name_arabic) + " " + str(rec.middle_name_arabic) + " " + str(rec.second_middle_name_arabic) + " " + str(rec.last_name_arabic),
                    'father_mobile_no':rec.father_mobile_no,
                    'mother_mobile_no':rec.mother_mobile_no,
                    'guardian_mobile_no':rec.guardian_mobile_no,
                    'national_id': rec.national_id,
                    'passport_id': rec.passport_id,
                    'nationality': rec.nationality.id,
                    'birth_date': rec.birth_date,
                    'birth_place': rec.birth_place,
                    'city': rec.city.id,
                    'address': rec.address,
                    'gender': rec.gender,
                    'religion': rec.religion,
                    'school_id': self.school_id.id,
                    'class_id': self.class_grade_id.id,
                    'class_section_id': self.section_id.id,
                    'prevous_school': rec.prevous_school,
                    'primary_language':rec.primary_language,
                    'second_language':rec.second_language,
                    'sibing_status': rec.sibing_status,
                    'mooddle_id':rec.mooddle_id,
                    'md_username':rec.md_username,
                    'md_password':rec.md_password,
                    'md_parent_username':rec.md_parent_username,
                    'moodle_status': 'active',
                    'state': 'draft',
                    'family_id': std_family.id,
                    'student_admission_form_id': rec.id,
                    'father_is_absent': rec.father_is_absent,
                    'father_full_name': str(rec.father_first_name or "") + ' ' + str(rec.father_middle_name or "") + ' ' + str(
                        rec.father_last_name or "") + ' ' + str(rec.father_fourth_name or ""),
                    'father_first_name': rec.father_first_name,
                    'father_middle_name': rec.father_middle_name,
                    'father_last_name': rec.father_last_name,
                    'father_fourth_name': rec.father_fourth_name,
                    'father_full_name_arabic': str(rec.father_first_name_arabic or "") + ' ' + str(
                        rec.father_middle_name_arabic or "") + ' ' + str(rec.father_last_name_arabic or "") + ' ' + str(
                        rec.father_fourth_name_arabic or ""),
                    'father_first_name_arabic': rec.father_first_name_arabic,
                    'father_middle_name_arabic': rec.father_middle_name_arabic,
                    'father_last_name_arabic': rec.father_last_name_arabic,
                    'father_fourth_name_arabic': rec.father_fourth_name_arabic,
                    'father_national_id': rec.father_national_id,
                    'father_passport': rec.father_passport,
                    'father_nationality': rec.father_nationality.id,
                    'father_marital_status': rec.father_marital_status,
                    'father_degree_education': rec.father_degree_education,
                    'father_employment': rec.father_employment,
                    'father_employer_location': rec.father_employer_location,
                    'father_landline_number': rec.father_landline_number,
                    'father_land_line_no': rec.father_land_line_no,
                    'father_mobile_no': rec.father_mobile_no,
                    'father_email': rec.father_email,
                    # mother
                    'mother_full_name': str(rec.mother_first_name or "") + ' ' + str(rec.mother_middle_name or "") + ' ' + str(
                        rec.mother_last_name or "") + ' ' + str(rec.mother_fourth_name or ""),
                    'mother_first_name': rec.mother_first_name,
                    'mother_middle_name': rec.mother_middle_name,
                    'mother_last_name': rec.mother_last_name,
                    'mother_fourth_name': rec.mother_fourth_name,
                    'mother_full_name_arabic': str(rec.mother_first_name_arabic or "") + ' ' + str(
                        rec.mother_middle_name_arabic or "") + ' ' + str(rec.mother_last_name_arabic or "") + ' ' + str(
                        rec.mother_fourth_name_arabic or ""),
                    'mother_first_name_arabic': rec.mother_first_name_arabic,
                    'mother_middle_name_arabic': rec.mother_middle_name_arabic,
                    'mother_last_name_arabic': rec.mother_last_name_arabic,
                    'mother_fourth_name_arabic': rec.mother_fourth_name_arabic,
                    'mother_national_id': rec.mother_national_id,
                    'mother_passport': rec.mother_passport,
                    'mother_nationality': rec.mother_nationality.id,
                    'mother_marital_status': rec.mother_marital_status,
                    'mother_degree_education': rec.mother_degree_education,
                    'mother_employment': rec.mother_employment,
                    'mother_employer_location': rec.mother_employer_location,
                    'mother_landline_number': rec.mother_landline_number,
                    'mother_land_line_no': rec.mother_land_line_no,
                    'mother_mobile_no': rec.mother_mobile_no,
                    'mother_email': rec.mother_email,
                    'mother_is_absent': rec.mother_is_absent,
                    # Guardian
                    'legal_guardian': rec.legal_guardian,
                    'guardian_full_name': str(rec.guardian_first_name or "") + ' ' + str(
                        rec.guardian_middle_name or "") + ' ' + str(rec.guardian_last_name or "") + ' ' + str(
                        rec.guardian_fourth_name or ""),
                    'guardian_first_name': rec.guardian_first_name,
                    'guardian_middle_name': rec.guardian_middle_name,
                    'guardian_last_name': rec.guardian_last_name,
                    'guardian_fourth_name': rec.guardian_fourth_name,
                    'guardian_full_name_arabic': str(rec.guardian_first_name_arabic or "") + ' ' + str(
                        rec.guardian_middle_name_arabic or "") + ' ' + str(rec.guardian_last_name_arabic or "") + ' ' + str(
                        rec.guardian_fourth_name_arabic or ""),
                    'guardian_first_name_arabic': rec.guardian_first_name_arabic,
                    'guardian_middle_name_arabic': rec.guardian_middle_name_arabic,
                    'guardian_last_name_arabic': rec.guardian_last_name_arabic,
                    'guardian_fourth_name_arabic': rec.guardian_fourth_name_arabic,
                    'guardian_national_id': rec.guardian_national_id,
                    'guardian_passport': rec.guardian_passport,
                    'guardian_nationality': rec.guardian_nationality.id,
                    'guardian_marital_status': rec.guardian_marital_status,
                    'relation_to_child': rec.relation_to_child,
                    'guardian_degree_education': rec.guardian_degree_education,
                    'guardian_employment': rec.guardian_employment,
                    'guardian_employeer_location': rec.guardian_employeer_location,
                    'guardian_landline_number': rec.guardian_landline_number,
                    'guardian_land_line_no': rec.guardian_land_line_no,
                    'guardian_mobile_no': rec.guardian_mobile_no,
                    'guardian_email': rec.guardian_email,

                    })

        rec.student_aca_stu_id = std_id.id
        
        std_class = self.env['student.class'].sudo().create({
                    'student_id': std_id.id,
                    'class_id': self.class_grade_id.id,
                    'class_section_id':self.section_id.id,
                    'status': 'active',
                    })
        
        if std_class:
            admission_id = self.env['student.admission.form'].search([('id', '=', rec.id)])
            if admission_id.state == 'documentation':
                rec.date_of_admission = datetime.now()
                rec.admitted_by = self._uid
                rec.state = 'payment'
        return

    def register_student_in_school_class_custom(self):
        sendingData = []
        recipientData = []
        if self.env.context.get('active_id') and self.env.context.get('active_model') == 'academic.student':
            admission_id = self.env.context.get('active_id')
            rec = self.env['academic.student'].browse(admission_id)
            info = {
                "name": rec['full_name'] if rec['full_name'] else '',
                "school_name": rec['school_id'].name if rec['school_id'] else '',
                "Class_name": rec['class_id'].name if rec['class_id'] else '',
                "std_user_name": rec.md_username if rec.md_username else '',
                "parent_user_name": rec.md_parent_username if rec.md_parent_username else '',
                "moodle_password": rec.md_password if rec.md_password else '',
            }
            sendingData.append(info)

            if len(sendingData) > 0:
                if rec.father_email:
                    recipientData.append(rec.father_email)
                if rec.mother_email:
                    recipientData.append(rec.mother_email)
                if rec.legal_guardian != 'father_is_legal_guardian':
                    if rec.guardian_email:
                        recipientData.append(rec.guardian_email)

                if self.env.company.admin_email:
                    recipientData.append(self.env.company.admin_email)

                else:
                    raise ValidationError(_("Please configure Admin Email Address!!!"))

                template = self.env.ref('sms_core.register_student_in_school_mail_template')
                email_value = {'email_to': ','.join(recipientData), 'email_from': self.env.user.email or '',
                               'subject': 'Admission:' + str(
                                   sendingData[0]['name']) or '--' + ',Admission Confirmed'}
                template.sudo().send_mail(admission_id, email_values=email_value, force_send=True)

            rec.school_id = self.school_id.id
            rec.class_id = self.class_grade_id.id
            rec.class_section_id = self.section_id
            rec.religion = self.religion
            rec.second_language = self.second_language
            rec.state = 'admitted'
            rec.student_admission_form_id.state = 'admitted'

    def action_change_student_class(self):
        parent_id = self.env.context.get('parent_id', False)
        rec = self.env['academic.student'].browse(parent_id)
        std_class_obj = rec.student_classes_ids
        std_courses_obj = rec.student_courses_ids
        for f in std_class_obj:
            if f.status == 'active':
                f.status = 'closed'
        for cr in std_courses_obj:
            if cr.course_status == 'active':
                cr.course_status = 'closed'
                
        std_class = self.env['student.class'].sudo().create({
                    'student_id': rec.id,
                    'class_id': self.class_grade_id.id,
                    'status': 'active',
                    })
    
    @api.onchange('school_id')
    def onchange_domain(self):
        # self.class_grade_id = ''
        self.class_course_ids = None
        ids_list_class_grade =[]
        if self.school_id:
            if not self.school_id.domain_name:
                raise UserError(_('Domain name is not set for school. Set a domain name on school form'))
        for f in  self.school_id.school_class_ids:
            ids_list_class_grade.append(f.id)
        return {'domain': {'class_grade_id': [('id', 'in', ids_list_class_grade)]}}
    
#     @api.onchange('class_grade_id')
#     def class_onchange_domain(self):
#         self.class_course_ids = None
#         class_course_ids_list =[]
#         course_list = self.env['class.course'].search([('class_id','=',self.class_grade_id.id),('active','=',True)])
#         for f in course_list:
#             class_course_ids_list.append(f.id)
#         self.class_course_ids = class_course_ids_list
#         return {'domain': {'class_course_ids': [('id', 'in', class_course_ids_list)]}}

    # we should comment this meth
    # @api.onchange('class_grade_id')
    # def class_onchange_domain(self):
    #     print(">>>>>>calling Method>>>>>>>>>>1111111111>>>>>>>>>", self)
    #     self.section_id = None
    #     class_section_ids_list =[]
    #     #the following 2 lines are commented due to client requ he wants classes should not be dependent on grades
    #     #sections_list = self.env['class.section'].search([('grade_id','=',self.class_grade_id.id)])
    #     #sections_list2 = self.env['class.section'].search([('grade_id','=',self.class_grade_id.id)],order='sequence_no')
    #
    #     sections_list = self.env['class.section'].search([])
    #     sections_list2 = self.env['class.section'].search([],order='sequence_no')
    #
    #     for rec in sections_list2:
    #         if rec.current_strength+1 <= rec.max_capacity:
    #             self.section_id = rec.id
    #             break
    #     for f in sections_list:
    #         class_section_ids_list.append(f.id)
    #     # self.class_section_ids = class_section_ids_list
    #     print(">>>>>>calling Method>>>>>>>>>>>self.section_id>>>>>>>>", self.section_id)
    #     return {'domain': {'section_id': [('id', 'in', class_section_ids_list)]}}

    @api.onchange('section_id')
    def section_onchange_domain(self):
        self.max_capacity = None
        self.current_strength = None
        print()
        for f in self.section_id:
            self.max_capacity = f.max_capacity
            self.current_strength = f.current_strength
        return
