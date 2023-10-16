# -*- coding: utf-8 -*-
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
import string
import re
# from doc._extensions.autojsdoc.parser.parser import _name


class SmsCore(models.Model):
    
    _name = 'student.admission.form'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Student Admission Form'
    _order = 'date_of_apply desc'
    
#     def unlink(self):
#         raise UserError(_('Deletion not allowed,use the (Cancel) option instead'))
#            
#         return 
    
    def action_get_hr_attachment_view(self):
        res = self.env['ir.actions.act_window'].for_xml_id('base', 'action_attachment')
        res['domain'] = [('res_model', '=', 'student.admission.form'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'student.admission.form', 'default_res_id': self.id}
        return res
    
    def _compute_attachment_docs(self):
        for emp in self:
            attachment_data = emp.env['ir.attachment'].search([('res_model', '=', 'student.admission.form'), ('res_id', 'in', emp.ids)])
            emp.attachment_docs = len(attachment_data)
    
    def print_report(self):
        data = {}
        data['form'] = self.read(['id'])[0]
        return self.env.ref('sms_core.action_std_admission_biodata_report').report_action(self, data=data, config=False)

    # def set_as_payment_for_interview(self):
    #     for stud in self:
    #         stud.state = 'admitted'

    def set_as_pending_for_interview(self):
        try:
            sendingData = []
            recipientData = []
            today = datetime.now()
            admission_id = self.env['student.admission.form'].search([('id', '=', self.id)])
            
            if admission_id.state == 'in_review':
                info = {
                    "name": admission_id['full_name'] if admission_id['full_name'] else '',
                }
                sendingData.append(info)

            if len(sendingData) > 0:
                if admission_id.father_email:
                    recipientData.append(admission_id.father_email)
                if admission_id.mother_email:
                    recipientData.append(admission_id.mother_email)
                if admission_id.legal_guardian != 'father_is_legal_guardian':
                    if admission_id.guardian_email:
                        recipientData.append(admission_id.guardian_email)

                template = self.env.ref('sms_core.interview_stage_mail')
                email_value = {'email_to': ','.join(recipientData), 'email_from': self.env.user.email or '',
                               'subject': 'Admission:' + str(sendingData[0]['name']) + ',Interview'}
                template.send_mail(admission_id.id, email_values=email_value, force_send=True)

                self.state = 'interview'

        except Exception as e:
            raise ValidationError(e)
    
        
    def set_as_pending_for_documents(self):

        try:
            sendingData = []
            recipientData = []
            today = datetime.now()
            current_month = today.strftime("%m")
            current_year = today.strftime("%Y")
            admission_id = self.env['student.admission.form'].search([('id', '=', self.id)])
            if admission_id.state == 'interview':
                info = {
                    "name": admission_id['full_name'] if admission_id['full_name'] else '',
                }
                sendingData.append(info)
#             managers = self.env['res.users'].search([('groups_id', '=', 'Employees / Manager'), ('active', '=', True)])
#             recipientData = [str(i.email) for i in managers if type(i.email) is not bool]
#             print(recipientData)
            if len(sendingData) > 0:
                if admission_id.father_email:
                    recipientData.append(admission_id.father_email)
                if admission_id.mother_email:
                    recipientData.append(admission_id.mother_email)
                if admission_id.legal_guardian != 'father_is_legal_guardian':
                    if admission_id.guardian_email:
                        recipientData.append(admission_id.guardian_email)

                template = self.env.ref('sms_core.document_stage_mail')
                email_value = {'email_to': ','.join(recipientData), 'email_from': self.env.user.email or '',
                               'subject': 'Admission:' + str(sendingData[0]['name']) + ',Document Submission'}
                if template:
                    template.send_mail(admission_id.id, email_values=email_value, force_send=True)

                self.state = 'documentation'
            
        except Exception as e:
            raise ValidationError(e)

    def cancel_application(self):
        try:
            sendingData = []
            recipientData = []
            today = datetime.now()
            admission_id = self.env['student.admission.form'].search([('id', '=', self.id)])
            if admission_id.state in ('in_review', 'interview', 'documentation', 'payment'):
                info = {
                    "name": admission_id['full_name'] if admission_id['full_name'] else '',
                }
                sendingData.append(info)
            if len(sendingData) > 0:
                if admission_id.father_email:
                    recipientData.append(admission_id.father_email)
                if admission_id.mother_email:
                    recipientData.append(admission_id.mother_email)
                if admission_id.legal_guardian != 'father_is_legal_guardian':
                    if admission_id.guardian_email:
                        recipientData.append(admission_id.guardian_email)

                template = self.env.ref('sms_core.cancellation_application_mail')
                email_value = {'email_to': ','.join(recipientData), 'email_from': self.env.user.email or '',
                               'subject': 'Admission:' + str(sendingData[0]['name']) + ',Interview'}
                template.send_mail(admission_id.id, email_values=email_value, force_send=True)

                self.state = 'cancelled'
                self.date_of_reject_cancel = datetime.now()
                self.rejected_by = self._uid

        except Exception as e:
            raise ValidationError(e)
        
    @api.onchange('legal_guardian')
    def check_legal_guardian_onchange(self):
        if self.legal_guardian == 'father_is_legal_guardian':
            if self.father_is_absent:
                self.legal_guardian = None
                
        elif self.legal_guardian == 'mother_is_legal_guardian':
            if self.mother_is_absent:
                self.legal_guardian = None
        if self.father_is_absent and self.mother_is_absent:
           self.legal_guardian = 'other' 
            
    @api.onchange('father_is_absent','mother_is_absent')
    def check_parents_absent_onchange(self):
        if self.father_is_absent: 
            if self.legal_guardian == 'father_is_legal_guardian':
                self.legal_guardian = None
                return
        if self.mother_is_absent: 
            if self.legal_guardian == 'mother_is_legal_guardian':
                self.legal_guardian = None
                return
        if self.mother_is_absent and self.father_is_absent: 
#             if self.legal_guardian == None:
            self.legal_guardian = 'other'
            return
    
    @api.depends('first_name', 'middle_name', 'second_middle_name', 'last_name')
    def _compute_student_name(self):
        for rec in self:
            rec.full_name = str(rec.first_name)+' '+str(rec.middle_name)+' '+str(rec.second_middle_name)+' '+str(rec.last_name) or ''

    @api.depends('first_name_arabic', 'middle_name_arabic', 'second_middle_name_arabic', 'last_name_arabic')
    def _compute_student_name_arabic(self):
        for rec in self:
            rec.full_name_arabic = str(rec.first_name_arabic) + " " + str(rec.middle_name_arabic) + " " + str(rec.second_middle_name_arabic) + " " + str(rec.last_name_arabic)

    def update_full_name_arabic(self):
        for student in self.search([]):
            first_name = student.first_name_arabic
            student.first_name_arabic = '-'
            student.first_name_arabic = first_name

    def update_full_name(self):
        for student in self.search([]):
            first_name = student.first_name
            student.first_name = '-'
            student.first_name = first_name

    # changes for code pushing
    # child fields:
    name = fields.Char('Student Name')
    application_no = fields.Char('Application No')
    full_name = fields.Char('Full Name', tracking=True, compute='_compute_student_name', store=True)
    first_name = fields.Char('First Name', required=True, tracking=True)
    middle_name = fields.Char('Middle Name')
    second_middle_name = fields.Char('Second Middle Name')
    last_name = fields.Char('Last Name', tracking=True)
    
    first_name_arabic = fields.Char('First Name Arabic', required=True, tracking=True)
    middle_name_arabic = fields.Char('Middle Name Arabic')
    second_middle_name_arabic = fields.Char('Second Middle Name Arabic')
    last_name_arabic = fields.Char('Last Name Arabic', tracking=True)
    
    full_name_arabic = fields.Char('Full Name Arabic', compute ='_compute_student_name_arabic', store=True)
    national_id = fields.Char('National ID', tracking=True)
    passport_id = fields.Char('Passport No', tracking=True)
    nationality = fields.Many2one('res.country', string='Nationality', tracking=True)
    birth_date = fields.Date('Date of Birth', tracking=True)
    birth_place = fields.Char('Birth Place')
    city = fields.Many2one('res.city')
    address = fields.Text('Address')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female'), ('other', 'Other')], default='male', required=True, string='Gender')

    religion = fields.Selection([('muslim', 'Muslim'), ('christian','Christian'),('other', 'Other')], default='muslim', string='Religion')
    student_image  = fields.Binary(string = 'Image',store=True,attachment=True)#application form
    attachment_docs = fields.Integer(compute='_compute_attachment_docs', string='Number of Attachments')
    # education = 
    application_for = fields.Selection([('american', 'American'), ('national', 'National'), ('ig', 'IG')], string='Application For')
    application_for_id = fields.Many2one('schools.list', string='Application For', tracking=True)
    school_id = fields.Many2one('schools.list', string='Admitted to School', tracking=True)
    class_id = fields.Many2one('school.class', string='Admitted to Grade', tracking=True, store=True, related="class_grade")
    school_name = fields.Char('School')
    class_grade = fields.Many2one('school.class',string='Admitted to Grade', tracking=True)
    prevous_school = fields.Char('Previous School')
    primary_language = fields.Char('Primary Language')
    second_language = fields.Char('Second Language')
    sibing_status = fields.Selection([('no_siblings', 'No Siblings'),('has_brothers_sisters', 'Brothers/Sisters in School'), ('staff_child', 'Staff Child')], default='no_siblings', string='Sibling Status')
    state = fields.Selection([('in_review', 'In Review'), ('interview', 'Interview'),
                              ('documentation', 'Documentation'), ('payment', 'Payment'),
                              ('admitted', 'Admitted'), ('rejected', 'Rejected'),
                              ('cancelled', 'Cancelled'), ('undecided','Undecided')],
                             'State',  default='in_review')
    date_of_apply = fields.Datetime('Date of Apply', default=datetime.now())
    date_of_admission = fields.Datetime('Date of Confirmation')
    date_of_reject_cancel = fields.Datetime('Date Reject Cancel')
    admitted_by = fields.Many2one('res.users', string='Confirmed By')
    rejected_by = fields.Many2one('res.users', string='Rejected By')
    # Fields (Father) 
    father_full_name = fields.Char('Father Full Name', tracking=True)
    father_full_name_arabic = fields.Char('Father Full Name Arabic')
    father_first_name = fields.Char('Father First Name', tracking=True)
    father_middle_name = fields.Char('Father Second Name')
    father_last_name = fields.Char('Father Third Name')
    father_fourth_name = fields.Char('Father Forth Name')
    father_passport = fields.Char('Passport No')
    father_first_name_arabic = fields.Char('Father First Name Arabic')
    father_middle_name_arabic = fields.Char('Father Second Name Arabic')
    father_last_name_arabic = fields.Char('Father Third Name Arabic')
    father_fourth_name_arabic = fields.Char('Father Forth Name Arabic')
    father_national_id = fields.Char('National ID', tracking=True)
    father_nationality = fields.Many2one('res.country', string='Nationality')
    father_marital_status = fields.Selection([('single', 'Single'), ('married', 'Married'), ('divorced', 'Divorced'), ('widow', 'Widow/widower')], string='Marital Status')
    father_degree_education = fields.Char('Education')
    father_employment = fields.Char('Employment')
    father_employer_location = fields.Char('Employment Location')
    father_landline_number = fields.Char('Home Phone')
    father_land_line_no = fields.Char('Work Phone')
    father_mobile_no = fields.Char('Mobile Number', tracking=True)
    father_email = fields.Char(string='Email')
    father_is_absent = fields.Boolean('Father is Absent')
    
    # Fields(Mother)
    mother_full_name = fields.Char('Mother Full Name', tracking=True)
    mother_full_name_arabic = fields.Char('Mother Full Name Arabic')
    mother_first_name = fields.Char('Mother First Name')
    mother_middle_name = fields.Char('Mother Second Name')
    mother_last_name = fields.Char('Mother Third Name')
    mother_fourth_name = fields.Char('Mother Forth Name')

    mother_first_name_arabic = fields.Char('Mother First Name Arabic')
    mother_middle_name_arabic = fields.Char('Mother Second Name Arabic')
    mother_last_name_arabic = fields.Char('Mother Third Name Arabic')
    mother_fourth_name_arabic = fields.Char('Mother Forth Name Arabic')
    mother_passport = fields.Char('Passport No')
    mother_national_id = fields.Char('National ID', tracking=True)
    mother_nationality = fields.Many2one('res.country', string='Nationality')
    mother_marital_status = fields.Selection([('single', 'Single'), ('married', 'Married'), ('divorced', 'Divorced'), ('widow', 'Widow/widower')], string='Marital Status')
    mother_degree_education = fields.Char('Education')
    mother_employment = fields.Char('Employment')
    mother_employer_location = fields.Char('Employment Location')
    mother_landline_number = fields.Char('Home Phone')
    mother_land_line_no = fields.Char('Work Phone')
    mother_mobile_no = fields.Char('Mobile Number', tracking=True)
    mother_email = fields.Char(string='Email')
    mother_is_absent = fields.Boolean('Mother is Absent')
    
    # Guardian Fields:
    legal_guardian = fields.Selection([('father_is_legal_guardian', 'Father is the legal guardian'), ('mother_is_legal_guardian', 'Mother is the legal guardian'), ('other', 'Other')], string='Legal Guardian')
    guardian_full_name = fields.Char('Guardian Full Name', tracking=True)
    guardian_full_name_arabic = fields.Char('Guardian Full Name Arabic')
    guardian_first_name = fields.Char('Guardian First Name')
    guardian_middle_name = fields.Char('Guardian Middle Name')
    guardian_last_name = fields.Char('Guardian Last Name')
    guardian_fourth_name = fields.Char('Guardian Fourth Name')
    guardian_first_name_arabic = fields.Char('Guardian First Name Arabic')
    guardian_middle_name_arabic = fields.Char('Guardian Middle Name Arabic')
    guardian_last_name_arabic = fields.Char('Guardian Last Name Arabic')
    guardian_fourth_name_arabic = fields.Char('Guardian Fourth Name Arabic')
    guardian_passport = fields.Char('Passport No')
    guardian_national_id = fields.Char('National ID', tracking=True)
    relation_to_child = fields.Char('Relation to The Child')
    guardian_nationality = fields.Many2one('res.country', string='Nationality')
    guardian_marital_status = fields.Selection([('single', 'Single'), ('married', 'Married'), ('divorced', 'Divorced'), ('widow', 'Widow/widower')], string='Marital Status')
    guardian_degree_education = fields.Char('Education')
    guardian_employment = fields.Char('Employment')
    guardian_employeer_location = fields.Char('Employment Location')
    guardian_landline_number = fields.Char('Home Phone')
    guardian_land_line_no = fields.Char('Work Phone')
    guardian_mobile_no = fields.Char('Mobile Number', tracking=True)
    guardian_email = fields.Char(string='Email')
    # Moodle Fields:
    md_parent_username = fields.Char('LMS Parent User Name')
    md_password = fields.Char('LMS Password')
    md_username = fields.Char('LMS User Name')
    mooddle_id = fields.Char('LMS ID', tracking=True)
    student_aca_stu_id = fields.Many2one('academic.student', 'Student')

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """
        Overridden name_search method to search based on name and code
        --------------------------------------------------------------
        :param self: object pointer
        :param name: the string typed in for searching the name
        :param args: the domain passed on the field
        :param operator: default is ilike so can search the matching string
        :param limit: max no of records
        """
        dom = ['|', '|', '|', '|', '|', '|', '|', '|', '|',
               ('first_name', operator, name), ('middle_name', operator, name),
               ('second_middle_name', operator, name), ('last_name', operator, name),
               ('full_name', operator, name), ('full_name_arabic', operator, name),
               ('first_name_arabic', operator, name), ('middle_name_arabic', operator, name),
               ('second_middle_name_arabic', operator, name), ('last_name_arabic', operator, name)]
        if args:
            dom += args
        student_name = self.search(dom, limit=limit)
        return student_name.name_get()

    @api.constrains('national_id', 'passport_id')
    def check_national_id_passport_id(self):
        """
        This method will check national id or passport id fill or not
        -------------------------------------------------------------
        @param self: object pointer
        """
        for student in self:
            if not student.national_id and not student.passport_id:
                raise ValidationError(_('Please Fill Either National ID or Passport No'))

    @api.constrains('father_national_id', 'father_passport')
    def check_father_national_id_passport_id(self):
        """
        This method will check father national id or passport id fill or not
        -------------------------------------------------------------
        @param self: object pointer
        """
        for student in self:
            if not student.father_national_id and not student.father_passport:
                raise ValidationError(_('Please Fill Either Father National ID or Father Passport No'))

    @api.constrains('mother_national_id', 'mother_passport')
    def check_mother_national_id_passport_id(self):
        """
        This method will check mother national id or passport id fill or not
        ----------------------------------------------------------------
        @param self: object pointer
        """
        for student in self:
            if not student.mother_national_id and not student.mother_passport:
                raise ValidationError(_('Please Fill Either Mother National ID or Mother Passport No'))

    @api.constrains('guardian_national_id', 'guardian_passport')
    def check_guardian_national_id_passport_id(self):
        """
        This method will check Guardian national id or Guardian Passport No fill or not
        -------------------------------------------------------------------------------
        @param self: object pointer
        """
        for student in self:
            if student.legal_guardian == 'other':
                if not student.guardian_national_id and not student.guardian_passport:
                    raise ValidationError(_('Please Fill Either Guardian National ID or Guardian Passport No'))

    @api.model
    def create(self, vals):

        ex_dict = {"national_id": '', "std_name": '', "status": '', }
        if vals.get('national_id'):
            exist = self.search([('national_id', '=', vals['national_id'])])
            if exist:
                exist = exist[0]
                ex_dict['national_id'] = exist.national_id
                ex_dict['std_name'] = exist.full_name
                ex_dict['status'] = exist.state
                return ex_dict

        count = self.env['student.admission.form'].search([])
        t_conut = len(count)
        appl_no = 'APPL' + str(t_conut).zfill(6)
        vals.update({'application_no': appl_no})

        if 'mother_is_guardian' in vals:
            if vals['mother_is_guardian'] == 'on':
                vals['legal_guardian'] = 'mother_is_legal_guardian'
                vals.pop("mother_is_guardian")

        elif 'father_is_guardian' in vals:
            if vals['father_is_guardian'] == 'on':
                vals['legal_guardian'] = 'father_is_legal_guardian'
                vals.pop("father_is_guardian")

        elif 'guardian_first_name' in vals:
            vals['legal_guardian'] = 'other'

        vals.update({'full_name': vals.get('first_name') or '' + ' ' + vals.get('middle_name') or '' + ' ' + vals.get(
            'second_middle_name') or '' + ' ' + vals.get('last_name') or ''})
        smscore_obj = super(SmsCore, self).create(vals)
        return smscore_obj

    # def set_as_pending_for_payment(self):
    #     for rec in self:
    #         rec.date_of_admission = datetime.now()
    #         rec.state = 'payment'

    def set_as_pending_for_payment(self):
        try:
            sendingData = []
            recipientData = []
            today = datetime.now()
            current_month = today.strftime("%m")
            current_year = today.strftime("%Y")
            admission_id = self.env['student.admission.form'].search([('id', '=', self.id)])
            if admission_id.state == 'documentation':
                info = {
                    "name": admission_id['full_name'] if admission_id['full_name'] else '',
                }
                sendingData.append(info)
#             managers = self.env['res.users'].search([('groups_id', '=', 'Employees / Manager'), ('active', '=', True)])
#             recipientData = [str(i.email) for i in managers if type(i.email) is not bool]
            print(recipientData)
            if len(sendingData) > 0:
                print("Sending date", sendingData)

                if admission_id.father_email:
                    recipientData.append(admission_id.father_email)
                if admission_id.mother_email:
                    recipientData.append(admission_id.mother_email)
                if admission_id.legal_guardian != 'father_is_legal_guardian':
                    if admission_id.guardian_email:
                        recipientData.append(admission_id.guardian_email)
                template = self.env.ref('sms_core.pending_payment_email_template')
                email_value = {'email_to': ','.join(recipientData), 'email_from': self.env.user.email or '',
                               'subject': 'Admission:' + str(sendingData[0]['name']) + ' Make Payment'}
                template.send_mail(self.id, email_values=email_value, force_send=True)

        except Exception as e:
            raise ValidationError(e)

        for rec in self:
            wizard_create = self.env['admit.student.school.wizard'].create({
                'school_id': rec.application_for_id.id,
                'class_grade_id': rec.class_grade.id,
            })
            wizard_create.register_student_in_school_class()


#     def write(self, vals):
#         re = super(SmsCore, self).write(vals)
#         res = self.env['student.admission.form'].browse(self.id)
#         full_name = res.full_name.split()
#         first_name = full_name[0]
#         last_name =' '
#         if len(full_name) >1:
#              last_name = full_name[1]
#         print("-----------full name------------",last_name,first_name)
#         parameters = '&users[0][id]=' + str(res.mooddle_id) + '&users[0][username]=' + str(res.md_username) + '&users[0][firstname]=' + str(first_name)+ '&users[0][lastname]=' + str(last_name)+ '&users[0][password]=' + str(res.md_password)   
#         moodle_url = 'http://35.192.148.38/webservice/rest/server.php?wstoken=ff5b4be8d6383ff175a5522805583246' + parameters + '&wsfunction=core_user_update_users&moodlewsrestformat=json'
#         head_params = {'wsfunction':'core_user_update_users', 'moodlewsrestformat':'json'}
#         response = requests.get(moodle_url, params=head_params)
#         response = response.json()
#         if response:
#             return res
    
class Followers(models.Model):
   _inherit = 'mail.followers'
   @api.model
   def create(self, vals):
        if 'res_model' in vals and 'res_id' in vals and 'partner_id' in vals:
            dups = self.env['mail.followers'].search([('res_model', '=',vals.get('res_model')),
                                           ('res_id', '=', vals.get('res_id')),
                                           ('partner_id', '=', vals.get('partner_id'))])
            if len(dups):
                for p in dups:
                    p.unlink()
        return super(Followers, self).create(vals)

class SchoolsList(models.Model): 
    
    _name = 'schools.list'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'schools.list'
    
    _sql_constraints = [('name_uniq', 'unique (name)', "School with same name already exists !")]
    
    def unlink(self):
        res = self.sync_erp_lms('class.section')
        print("this is the school unlink method",res)
#         if self.active == True:
#         raise UserError(_('Deletion are not allowed on ERP.'))
#         else:
#             rec = super(SchoolsList, self).unlink()    
#         return rec
        return
    def menu_item_sync_erp_lms(self):
        print("menu_item_sync_erp_lms")
        tb_ls =  ['class.section','schools.list']
        for f in tb_ls:
            res = self.sync_erp_lms(f,'called from cron job')
            print("This is the reponse of menu item sync erp lms",res)
    
    school_id = fields.Integer('School ID')
    name = fields.Char('School Name', required=True, tracking=True)
    domain_name = fields.Char('Domain Name', required=True, tracking=True,default = 'gmail.com')
    school_type = fields.Selection([('pre_school', 'Pre School'), ('primary', 'Primary'), ('secondary', 'Secondary'), ('higher_secondary', 'Higher Secondary')],default='pre_school', string='School Type')
    school_description = fields.Text('Description')
    moodle_id = fields.Char('Moodle ID', tracking=True)
    active = fields.Boolean('Active', tracking=True,default=True)
    school_class_ids = fields.One2many('school.class', 'school_id')
    school_students_ids = fields.One2many('academic.student', 'school_id', string='Students')
    lms_status = fields.Selection([('synced', 'Synced'), ('not_synced', 'Not Synced'), ('in_active', 'Inactive'), ('deleted', 'Deleted')], string='Lms Status')
    
    def sync_erp_lms(self,table_md,reqt_source):
        if self.env.company.synced_with_lms:
            if table_md == 'schools.list':
                lms_school_lst =[]
                lms_class_lst = []
                parameters = ''
                moodle_url = 'http://'+self.env.company.lms_url+'/webservice/rest/server.php' + '?wstoken=' + self.env.company.lms_url_token + parameters + '&wsfunction=core_course_get_categories&moodlewsrestformat=json'
                head_params = {'wsfunction':'core_course_get_categories', 'moodlewsrestformat':'json'}
                response = requests.get(moodle_url, params=head_params)
                response = response.json()
                print("this is the get category response",response)
                for f in response:
                    print("response for each",f['name'])
                    if f['parent'] == 0:
                        print("no patent")
                        lms_school_lst.append(f['id'])
                        rec_exist = self.env['schools.list'].search([('moodle_id','=',f['id'])])
                        if not rec_exist:
                            self.env['schools.list'].create({
                            'name': f['name'],
                            'school_description': f['name'],
                            'moodle_id':f['id'],
                            'lms_status': 'synced'})
                        else:
                            rec_exist.name = f['name']
                    else:
                        print("child")
                        lms_class_lst.append(f['id'])
                        cls_exist = self.env['school.class'].search([('mooddle_id','=',f['id'])])
                        if not cls_exist:
                            parent_rec = self.env['schools.list'].search([('moodle_id','=',f['parent'])])
                            self.env['school.class'].create({
                            'name': f['name'],
                            'desc': f['name'],
                            'mooddle_id':f['id'],
                            'school_id':parent_rec.id,
                            'cls_lms_status': 'synced'})
                        else:
                            cls_exist.name = f['name']
                not_exist = self.env['schools.list'].search([('moodle_id','not in',lms_school_lst)])
                for t in not_exist:
                    t.lms_status = 'deleted'
                cls_not_exist = self.env['school.class'].search([('mooddle_id','not in',lms_school_lst)])
                for t in cls_not_exist:
                    t.cls_lms_status = 'deleted'
            elif table_md == 'class.section':
                lms_cls_sec_lst =[]
                parameters = ''
                moodle_url = 'http://'+self.env.company.lms_url+'/webservice/rest/server.php' + '?wstoken=' + self.env.company.lms_url_token + parameters + '&wsfunction=core_cohort_get_cohorts&moodlewsrestformat=json'
                head_params = {'wsfunction':'core_cohort_get_cohorts', 'moodlewsrestformat':'json'}
                response = requests.get(moodle_url, params=head_params)
                response = response.json()
                print("response will print here",response)
                for f in response:
                    if f['name']:
                        lms_cls_sec_lst.append(f['id'])
                        sec_rec_exist = self.env['class.section'].search([('mooddle_id','=',f['id'])])
                        print("this is the sec_rec_exist",sec_rec_exist)
                        if not sec_rec_exist:
                            sec_rec_exist.create({'name': f['name'],
                                              'mooddle_id': f['id'],
                                              'cls_sec_lms_status': 'synced'})
                        else:
                            sec_rec_exist.name = f['name']
                cls_sec_n_exist = self.env['class.section'].search([('mooddle_id','not in',lms_cls_sec_lst)])
                for t in cls_sec_n_exist:
                    t.cls_sec_lms_status = 'deleted'
            return
    
#     def display_lms_status(self):
#         if self.moodle_id == None:
#             self.lms_status = 'not_synced'
#         else:
#             self.lms_status = 'synced'
#         return

#     @api.model
#     def create(self, vals):
#         schools_obj = super(SchoolsList, self).create(vals)
#         try:
#             parameters = '&categories[0][name]=' + str(vals['name']) + '&categories[0][parent]=' + str(0) + '&categories[0][description]=' + str(vals['school_description'])
#             moodle_url = 'http://35.192.148.38/webservice/rest/server.php?wstoken=ff5b4be8d6383ff175a5522805583246' + parameters + '&wsfunction=core_course_create_categories&moodlewsrestformat=json'
#             head_params = {'wsfunction':'core_course_create_categories', 'moodlewsrestformat':'json'}
#             response = requests.get(moodle_url, params=head_params)
#             response = response.json()
#             if response:
#                 response = response[0]
#             if 'id' in response:
#                 schools_obj.moodle_id = response['id']
#         except:
#             raise UserError(_('Category! Record not created on lms contact your system administrator'))
#         return schools_obj
    
    
    
    
    
    def cron_sync_erp_lms(self):
        print("cron job is called for erp lms sync")
        tb_ls =  ['class.section','schools.list']
        for f in tb_ls:
            res = self.sync_erp_lms(f,'called from cron job')
            print("This is the reponse of cron sync erp lms",res)
            
    
class SchoolClass(models.Model):
    
    _name = 'school.class'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'school.class'
    
     
    name = fields.Char(string='Grade', required=True, tracking=True) 
    desc = fields.Char(string='Description')
    grading_policy = fields.Char(string='Grading Policy')  # it will be one2many with'sms.grading.policy'
    sequence = fields.Integer(string='Sequence No') 
    school_id = fields.Many2one('schools.list', strgin="School", require=True)
    courses_ids = fields.One2many('class.course', 'class_id', string="Courses")
    students_ids = fields.One2many('academic.student', 'class_id', string="Students")
    active = fields.Boolean('Active', default=True, tracking=True)
    mooddle_id = fields.Char('Moodle ID', tracking=True)
    cls_lms_status = fields.Selection([('synced', 'Synced'), ('not_synced', 'Not Synced'), ('in_active', 'Inactive'), ('deleted', 'Deleted')], string='Lms Status')
    def unlink(self):
        raise UserError(_('Deletion are not allowed on ERP.'))
    
    
    
    def sync_cohort_student_with_erp(self):
        print("sync_cohort_student_with_erp method is called")
        if self.env.company.synced_with_lms:
            for i in self.env['class.section'].search([('sync','=',True)]):
                if True:
                    parameters = '&cohortids[0]='+str(i.mooddle_id)
                    moodle_url = 'http://'+self.env.company.lms_url+'/webservice/rest/server.php' + '?wstoken=' + self.env.company.lms_url_token +  parameters + '&wsfunction=core_cohort_get_cohort_members&moodlewsrestformat=json'
                    head_params = {'wsfunction':'core_cohort_get_cohort_members', 'moodlewsrestformat':'json'}
                    response = requests.get(moodle_url, params=head_params)
                    response = response.json()
                    response = response[0]
                    print("LMS response Cohorts",response)


                    if 'userids' in response:
                        cohortid = response['cohortid']
                        class_id = self.env['class.section'].search([('mooddle_id','=',cohortid)])
                        erp_student = self.env['academic.student'].search([('class_section_id','=',class_id.id)])

                        for s in erp_student:
                            s.class_section_id = None


                        for mod in response['userids']:
                            std_exist = self.env['academic.student'].search([('mooddle_id','=',mod)])
                            if std_exist:
                                std_exist.class_section_id = class_id.id
                            else:
                                adm_exist = self.env['academic.student'].search([('mooddle_id','=',mod)])
                                if not adm_exist:
                                    parameters = '&criteria[0][key]=id&criteria[0][value]='+str(mod)
                                    moodle_url = 'http://'+self.env.company.lms_url+'/webservice/rest/server.php' + '?wstoken=' + self.env.company.lms_url_token + parameters + '&wsfunction=core_user_get_users&moodlewsrestformat=json'
                                    head_params = {'wsfunction':'core_user_get_users', 'moodlewsrestformat':'json'}
                                    response = requests.get(moodle_url, params=head_params)
                                    response = response.json()

                                    if 'users'in response:
                                        user_info = response['users'][0]
                                        rec  = self.env['student.admission.form'].create({
                                            'full_name':user_info['firstname'],
                                            'md_username':user_info['username'],
                                            'mooddle_id':user_info['id'],
                                            'national_id':user_info['id'],
                                            'class_id':class_id.grade_id.id,
                                            'school_id':class_id.grade_id.school_id.id,
                                            'state':'undecided',
                                            })
                                        print("result",rec)

    #             except:
    #                 raise UserError(_('Not sync with lms contact your system administrator'))
            return

    
    @api.model
    def create(self, vals):
        response = {'debuginfo':''}
        class_obj = super(SchoolClass, self).create(vals)
#         if class_obj:
#             school_moodle_id = class_obj.school_id.moodle_id
# #             if not school_moodle_id:
#                 raise UserError(_('LMS ID Not Found for School'+str(class_obj.school_id))
#             #old code to create class using moodle categories
#             parameters = '&categories[0][name]=' + str(vals['name']) + '&categories[0][parent]=' + str(school_moodle_id) + '&categories[0][description]=' + str(vals['desc'])
#             moodle_url = 'http://35.192.148.38/webservice/rest/server.php?wstoken=ff5b4be8d6383ff175a5522805583246' + parameters + '&wsfunction=core_course_create_categories&moodlewsrestformat=json'
#             head_params = {'wsfunction':'core_course_create_categories', 'moodlewsrestformat':'json'}
#                         
#             response = requests.get(moodle_url, params=head_params)
#             response = response.json()
#             print("response",response)
#             if response:
#                 response = response[0]
#             if 'errorcode' in response:
#                 raise UserError(_('%s') % (response['debuginfo']))
#             elif 'id' in response:
#                 class_obj.mooddle_id = response['id']
#             return class_obj
#         else:
        return class_obj
        

class ClassSection(models.Model):
    
    _name = 'class.section'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'class.section'

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None, ):
        context = dict(self._context) or {}
        args = args or []
        if context.get("class_grade_id"):
            self._cr.execute("""
                select
                    id
                from
                    class_section
                where
                    grade_id = %s
            """, (context.get("class_grade_id"),))
            section_ids = [section_id[0] for section_id in self._cr.fetchall() if section_id]
            if section_ids:
                args += [("id", "in", section_ids)]
            else:
                args += [("grade_id", "=", False)]
        return super()._search(args, offset=offset, limit=limit, order=order, count=count,
                                   access_rights_uid=access_rights_uid,)

    @api.model
    def create(self, vals):
        if 'grade_id' in vals:
            
            if vals['grade_id']:
                _sql = """SELECT COALESCE(MAX(sequence_no),'0') FROM class_section
                              WHERE grade_id = """+str(vals['grade_id'])+ """ """
        else:
            _sql = """SELECT COALESCE(MAX(sequence_no),'0') FROM class_section """
              
        self.env.cr.execute(_sql)
        max_no = self.env.cr.fetchone()[0]
        print("No is +++++",max_no)
        vals['sequence_no'] = max_no + 1
        class_obj = super(ClassSection, self).create(vals)
        return class_obj
    
    def get_current_strength(self):
        
        for f in self:
            count = self.env['academic.student'].search([('class_section_id','=',f.id),('class_id','=',f.grade_id.id)])
            print("this is count ==== ",count)
            f.current_strength = len(count)
    
    name = fields.Char(string='Class', required=True, tracking=True)
    grade_id = fields.Many2one('school.class', string='Grade', tracking=True)
    sequence_no = fields.Integer(string='Sequence No')
    max_capacity = fields.Integer(string='Max Capacity', tracking=True,default="40")
    current_strength = fields.Integer(string='Current Strength', compute='get_current_strength')
    student_ids = fields.One2many('academic.student', 'class_section_id', string="Students")
    mooddle_id = fields.Char('Moodle ID', tracking=True)
    cls_sec_lms_status = fields.Selection([('synced', 'Synced'), ('not_synced', 'Not Synced'), ('in_active', 'Inactive'), ('deleted', 'Deleted')], string='Lms Status')
    sync = fields.Boolean('Sync')
#     def unlink(self):
#         raise UserError(_('Deletion are not allowed on ERP.'))
    
    #CODE COMMENTED DUE TO STRUCTURE CHANGES
#     def unlink(self):
#         try:
#             print("this is the deleted id",self.mooddle_id)
#             parameters = '&cohortids[0]='+str(self.mooddle_id)
#             moodle_url = 'http://35.192.148.38/webservice/rest/server.php?wstoken=ff5b4be8d6383ff175a5522805583246' + parameters + '&wsfunction=core_cohort_delete_cohorts&moodlewsrestformat=json'
#             head_params = {'wsfunction':'core_cohort_delete_cohorts', 'moodlewsrestformat':'json'}
#             response = requests.get(moodle_url, params=head_params)
#             response = response.json()
#             print("Cohort delete API Response",response)
#             if response == None:
#                 print("Cohort Deleted Successfully")
#         except:
#              raise UserError(_('Cohort! Record not Deleted on lms contact your system administrator'))
#         rec = super(ClassSection, self).unlink() 
#         return rec
    
#     @api.model
#     def create(self, vals):
#         class_obj = super(ClassSection, self).create(vals)
#         try:
#             parameters = '&cohorts[0][idnumber]='+str(class_obj.id)+\
#                  '&cohorts[0][categorytype][type]=system'+\
#                  '&cohorts[0][categorytype][value]='+str(class_obj.grade_id.mooddle_id)+\
#                  '&cohorts[0][name]='+str(class_obj.name)+\
#                  '&cohorts[0][descriptionformat]=1'+\
#                  '&cohorts[0][visible]=1'+\
#                  '&cohorts[0][description]='+str(class_obj.name)
#             moodle_url = 'http://35.192.148.38/webservice/rest/server.php?wstoken=ff5b4be8d6383ff175a5522805583246' + parameters + '&wsfunction=core_cohort_create_cohorts&moodlewsrestformat=json'
#             head_params = {'wsfunction':'core_cohort_create_cohorts', 'moodlewsrestformat':'json'}
#             response = requests.get(moodle_url, params=head_params)
#             response = response.json()
#             print("response--------",response)
#             if response:
#                 response = response[0]
#             if 'id' in response:
#                 class_obj.mooddle_id = response['id']
#         except:
#             raise UserError(_('Cohort! Record not created on lms contact your system administrator'))
#         return class_obj

#     def write(self, vals):
#         print("write method is called",vals)
#         res = super(ClassSection, self).write(vals)
#         class_obj = self.env['class.section'].browse(self.id)
#         try:
#             parameters = '&cohorts[0][id]='+str(class_obj.mooddle_id)+\
#                  '&cohorts[0][idnumber]='+str(class_obj.id)+\
#                  '&cohorts[0][categorytype][type]=system'+\
#                  '&cohorts[0][categorytype][value]='+str(class_obj.grade_id.mooddle_id)+\
#                  '&cohorts[0][name]='+str(class_obj.name)+\
#                  '&cohorts[0][descriptionformat]=1'+\
#                  '&cohorts[0][visible]=1'+\
#                  '&cohorts[0][description]='+str(class_obj.name)
#             moodle_url = 'http://35.192.148.38/webservice/rest/server.php?wstoken=ff5b4be8d6383ff175a5522805583246' + parameters + '&wsfunction=core_cohort_update_cohorts&moodlewsrestformat=json'
#             head_params = {'wsfunction':'core_cohort_update_cohorts', 'moodlewsrestformat':'json'}
#             response = requests.get(moodle_url, params=head_params)
#             response = response.json()
#             print("response----Updated---cohort-",response)
#         except:
#             raise UserError(_('Cohort! Record not Updated on lms contact your system administrator'))
#         return res



    
class CourseRepository(models.Model):
    
    _name = 'course.repository'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'course.repository'
    
    name = fields.Char(string='Course', required=True, tracking=True) 
    desc = fields.Char(string='Description')
    active = fields.Boolean('Active', default=True, tracking=True)
    sequence = fields.Integer(string='Sequence No')

class ClassCourses(models.Model):
    
    _name = 'class.course'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'class.course'
    
    name = fields.Many2one('course.repository', string='Course', required=True, tracking=True)
    class_id = fields.Many2one('school.class', string='Grade', required=True) 
    desc = fields.Char(string='Description')
    active = fields.Boolean('Active', tracking=True)
    mooddle_id = fields.Char('Moodle ID', tracking=True)
    
    
    @api.model
    def create(self, vals):
        response={'message':''}
        schools_obj = super(ClassCourses, self).create(vals)
        #the following code is commented on 12 jul by shahid due to the client requirements that classes, grades and 
        #schools will be crated from moodle side, and will fetched in odoo
        #when there is a need to uncomment this code, the try block should contain only the call to api
        #rest of the code should be outside of try block
#         try:
#             
#             parameters= '&courses[0][fullname]='+str(schools_obj.name.name)+'&courses[0][categoryid]='+str(int(schools_obj.class_id.mooddle_id))+'&courses[0][shortname]='+str(schools_obj.name.name+str(schools_obj.id))
#             moodle_url = 'http://35.192.148.38/webservice/rest/server.php?wstoken=ff5b4be8d6383ff175a5522805583246'+parameters+'&wsfunction=core_course_create_courses&moodlewsrestformat=json'
#             head_params = {'wsfunction':'core_course_create_courses', 'moodlewsrestformat':'json'}
#             response = requests.get(moodle_url, params=head_params)
#             response = response.json()
#             print("Response ClassCourses",response)
#             if response:
#                 if 'errorcode' in response:
#                     raise UserError(_('%s') % (response['message']))
#                 else:
#                     response = response[0]
#                     if 'id' in response:
#                         schools_obj.mooddle_id = response['id']
#                         return schools_obj
#         except:
#             print("This is the Exception point")
#             raise UserError(_('%s') % (response['message']))
        return


class AcademicStudent(models.Model):
    _name = "academic.student"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "academic.student"
    _rec_name = 'full_name'

    def _set_sibling_father_mother_active_emp(self):
        national_dict = {}
        passport_dict = {}
        students = self.search([('state', 'not in', ['cancelled', 'withdrawn'])])
        emp_obj = self.env['hr.employee']
        employees = emp_obj.search([])
        national_ids = employees.mapped('national_id')
        passport_ids = employees.mapped('passport_id')
        for student in students:
            student.father_active_employee = False
            student.mother_active_employee = False
            student.father_employee_id = False
            student.mother_employee_id = False
            if student.father_national_id and student.father_national_id in national_ids:
                student.father_active_employee = True
                student.father_employee_id = emp_obj.search([('national_id', '=', student.father_national_id)])
            if student.mother_national_id and student.mother_national_id in national_ids:
                student.mother_active_employee = True
                student.mother_employee_id = emp_obj.search([('national_id', '=', student.mother_national_id)])
            if student.father_passport and student.father_passport in passport_ids:
                student.father_active_employee = True
                student.father_employee_id = emp_obj.search([('passport_id', '=', student.father_passport)])
            if student.mother_passport and student.mother_passport in passport_ids:
                student.mother_active_employee = True
                student.mother_employee_id = emp_obj.search([('passport_id', '=', student.mother_passport)])
            if student.father_national_id:
                if student.father_national_id in national_dict.keys():
                    national_dict.get(student.father_national_id).append(student.id)
                else:
                    national_dict.update({student.father_national_id: [student.id]})
            elif student.mother_national_id:
                if student.mother_national_id in national_dict.keys():
                    national_dict.get(student.mother_national_id).append(student.id)
                else:
                    national_dict.update({student.mother_national_id: [student.id]})
            elif student.father_passport:
                if student.father_passport in national_dict.keys():
                    passport_dict.get(student.father_passport).append(student.id)
                else:
                    passport_dict.update({student.father_passport: [student.id]})
            elif student.mother_passport:
                if student.mother_passport in national_dict.keys():
                    passport_dict.get(student.mother_passport).append(student.id)
                else:
                    passport_dict.update({student.mother_passport: [student.id]})
        for student in students:
            student.write({'siblings_ids': [(5, 0, 0)]})
            sibling_lst = []
            if student.father_national_id:
                for rec in national_dict.get(student.father_national_id):
                    if rec != student.id:
                        sibling_lst.append((4, rec))
            elif student.mother_national_id:
                for rec in national_dict.get(student.mother_national_id):
                    if rec != student.id:
                        sibling_lst.append((4, rec))
            elif student.father_passport:
                for rec in passport_dict.get(student.father_passport):
                    if rec != student.id:
                        sibling_lst.append((4, rec))
            elif student.mother_passport:
                for rec in passport_dict.get(student.mother_passport):
                    if rec != student.id:
                        sibling_lst.append((4, rec))
            student.write({'siblings_ids': sibling_lst})


    @api.constrains('father_national_id', 'father_passport')
    def check_father_national_id_or_passport_id(self):
        """
        This method will check father national id or passport id fill or not
        -------------------------------------------------------------
        @param self: object pointer
        """
        for student in self:
            if not student.father_national_id and not student.father_passport:
                raise ValidationError(_('Please Fill Either Father National ID or Father Passport No'))

    @api.constrains('mother_national_id', 'mother_passport')
    def check_mother_national_id_or_passport_id(self):
        """
        This method will check mother national id or passport id fill or not
        ----------------------------------------------------------------
        @param self: object pointer
        """
        for student in self:
            if not student.mother_national_id and not student.mother_passport:
                raise ValidationError(_('Please Fill Either Mother National ID or Mother Passport No'))

    @api.constrains('guardian_national_id', 'guardian_passport')
    def check_guardian_national_id_or_passport_id(self):
        """
        This method will check Guardian national id or Guardian Passport No fill or not
        -------------------------------------------------------------------------------
        @param self: object pointer
        """
        for student in self:
            if student.legal_guardian == 'other':
                if not student.guardian_national_id and not student.guardian_passport:
                    raise ValidationError(_('Please Fill Either Guardian National ID or Guardian Passport No'))

    def change_student_class(self):
        rec_exist = self.env['student.class'].search([('student_id','=',self.id),('status','=','active')])
        if self.state == 'admitted':
            if rec_exist:
                form_id = self.env.ref('sms_core.view_admit_student_school_wizard', False)
                return {
                'name': 'Update Student Class',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'admit.student.school.wizard',
                'view_id'   : form_id.id,
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context'   :{
                    'default_line_rec_id':self.id,
                    'default_parent_id':self.id,
                              'default_school_id':rec_exist.class_id.school_id.id,
                              'default_class_grade_id': rec_exist.class_id.id,
                              'default_class_course_ids':rec_exist.class_id.courses_ids.ids,
                            'default_wizard_mode': 'academic_student'
                              }}
    
    
    def unlink(self):
        raise UserError(_('Student should not be deleted, use the option of withdrawal instead.'))
    
    def withdraw_student(self):
        std_class = self.env['student.class'].search([('student_id','=',self.id),('status','=','active')])
        for cls in std_class:
            cls.status = 'withdrawn'
        std_courses = self.env['student.courses'].search([('student_id','=',self.id),('course_status','=','active')])
        for course in std_courses:
            course.course_status = 'withdrawn'
        self.state = 'withdrawn'
        self.date_of_withdraw = datetime.today()  
        self.withdraw_by =  self._uid
        try:
            if self.env.company.synced_with_lms:
                parameters = '&members[0][cohortid]='+str(std_class.class_id.mooddle_id)+\
                             '&members[0][userid]='+str(self.mooddle_id)
                moodle_url = 'http://'+self.env.company.lms_url+'/webservice/rest/server.php' + '?wstoken=' + self.env.company.lms_url_token + parameters + '&wsfunction=core_cohort_delete_cohort_members&moodlewsrestformat=json'
                head_params = {'wsfunction':'core_cohort_delete_cohort_members', 'moodlewsrestformat':'json'}
                response = requests.get(moodle_url, params=head_params)
                response = response.json()
                print("Delete cohort member",response)
        except:
            raise UserError(_('Record not deleted on lms contact your system administrator'))
        return
    
    
    def cron_deactive_lms(self):
        """
        This method is called, by a cron job to de-activate defaulter student on lms.
        """
        std_lst = []
        flg = 'in_active' 
        today_date = datetime.now().date()
        #FOR DEACTIVATION OF DEFAULTER STUDENTS
        std_fee = self.env['student.fee'].search([('is_overdue','=',True),('warning_date','<',today_date)])
        for f in std_fee:
            if f not in std_lst:
                std_lst.append(f.student_id.id)
                res = self.active_inactive_student(f.student_id,'Fee_defaulter',flg)
        #FOR ACTIVATION OF DEACTIVE STUDENTS    
        std_ids = self.env['academic.student'].search([('moodle_status','=','in_active'),('reason','=','Fee_defaulter')])   
        for std in std_ids:  
            for f in std.student_fee_ids:
                if not f.is_overdue:
                    flg = 'active'
                    res = self.active_inactive_student(f.student_id,'clear',flg)
                    continue
        return 
    
    
    def active_inactive_student(self,std_id,reason,flg):
        """
        This is central method called from cron jobs also from a wizrd, used to 
        activat and de-activate student from lms
        """
        suspended =1
        std_id.reason = reason
        if flg =='in_active':
            message = "Student not deactivated on lms contact your system administrator"
            std_id.moodle_status = 'in_active' 
            if reason =='Fee_defaulter': 
                recipientData = []
                std_email =''
                if std_id.father_email:
                    std_email = std_id.father_email
                elif std_id.mother_email:
                    std_email = std_id.mother_email
                else :
                    std_email = std_id.guardian_email
                if not std_email:
                    raise UserError(_('Email address is missing.'))
                recipientData.append(std_email)
                template = self.env.ref('sms_core.deactivation_lms_mail_template')
                email_value = {'email_to': ','.join(recipientData), 'email_from': self.env.user.email or '',
                               'subject': 'LMS Account Deactivated'}
                template.send_mail(std_id.id, email_values=email_value, force_send=True)
        else:
            suspended = 0
            std_id.moodle_status = 'active'
            message = "Student not activated on lms contact your system administrator"
        try:
            if self.env.company.synced_with_lms:
                parameters = '&users[0][id]=' + str(std_id.mooddle_id) + '&users[0][suspended]=' + str(suspended)
                moodle_url = 'http://'+self.env.company.lms_url+'/webservice/rest/server.php' + '?wstoken=' + self.env.company.lms_url_token + parameters + '&wsfunction=core_user_update_users&moodlewsrestformat=json'
                head_params = {'wsfunction':'core_user_update_users', 'moodlewsrestformat':'json'}
                response = requests.get(moodle_url, params=head_params)
                response = response.json()
                print("ACTIVE INACTIVE STUDENT METHOD UPDATE API RESPONSE",response)

        except:
            raise UserError(_(message))
        return 


    def compute_student_unique_id(self):
        for std in self:
            std.student_id = str(std.id).zfill(6)
        return
    
    # child fields:
    @api.depends('first_name', 'middle_name', 'second_middle_name', 'last_name')
    def _compute_student_name(self):
        for std in self:
            std.full_name = str(std.first_name)+' '+str(std.middle_name)+' '+str(std.second_middle_name)+' '+str(std.last_name) or ''

    @api.depends('first_name_arabic', 'middle_name_arabic', 'second_middle_name_arabic', 'last_name_arabic')
    def _compute_student_name_arabic(self):
        for std in self:
            std.full_name_arabic = str(std.first_name_arabic) + " " + str(std.middle_name_arabic) + " " + str(std.second_middle_name_arabic) + " " + str(std.last_name_arabic)

    def update_full_name_arabic(self):
        for student in self.search([]):
            first_name = student.first_name_arabic
            student.first_name_arabic = '-'
            student.first_name_arabic = first_name

    def update_full_name(self):
        for student in self.search([]):
            first_name = student.first_name
            student.first_name = '-'
            student.first_name = first_name

    # child fields:
    # photo
    name = fields.Char('Student Name')
    partner_id = fields.Many2one('res.partner', 'Customer')
    full_name = fields.Char('Full Name', tracking=True, store=True, compute='_compute_student_name')
    first_name = fields.Char('First Name', required=True, tracking=True)
    middle_name = fields.Char('Middle Name')
    second_middle_name = fields.Char('Second Middle Name')
    last_name = fields.Char('Last Name', tracking=True)
    payment_status = fields.Selection([('not_paid', 'Not paid'), ('paid', 'Paid')], default='not_paid',
                                      string='Payment Status')
    
    first_name_arabic = fields.Char('First Name Arabic', required=True, tracking=True)
    middle_name_arabic = fields.Char('Middle Name Arabic')
    second_middle_name_arabic = fields.Char('Second Middle Name Arabic')
    last_name_arabic = fields.Char('Last Name Arabic', tracking=True)
    
    student_image  = fields.Binary(string = 'Image',store=True,attachment=True)#academic.student table
    full_name_arabic = fields.Char('Full Name Arabic', compute='_compute_student_name_arabic', store=True)
    student_id = fields.Char('Student ID', compute='compute_student_unique_id')
    national_id = fields.Char('National ID', tracking=True)
    passport_id = fields.Char('Passport No', tracking=True)
    nationality = fields.Many2one('res.country', string='Nationality', tracking=True)
    birth_date = fields.Date('Date of Birth', tracking=True)
    birth_place = fields.Char('Birth Place')
    city = fields.Many2one('res.city')
    address = fields.Text('Address')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female'), ('other', 'Other')], default='male', required=True, string='Gender')
    religion = fields.Selection([('muslim', 'Muslim'), ('christian','Christian'),('other', 'Other')], default='muslim', string='Religion')
    student_classes_ids = fields.One2many('student.class', 'student_id', string='Classes')
    student_courses_ids = fields.One2many('student.courses', 'student_id', string='Student Courses')
    student_fee_ids = fields.One2many('student.fee', 'student_id', string='Student Fee')
    select_student = fields.Boolean('Select Student')
    siblings_ids = fields.Many2many('academic.student', 'acad_stud_sibling_rel', 'student_id', 'sibling_id',
                                    string='Siblings')

    # parent employee
    mother_employee_id = fields.Many2one('hr.employee', string='Mother Employee')
    father_employee_id = fields.Many2one('hr.employee', string='Father Employee')

    # education = 
    admission_date = fields.Date('Admission Date')
    # application_for = fields.Selection([('american', 'American'), ('national', 'National'), ('ig', 'IG')], string='Application For')
    class_id = fields.Many2one('school.class', string='Grade', tracking=True)
    class_section_id = fields.Many2one('class.section', string='Section', tracking=True)
    school_id = fields.Many2one('schools.list', string='School', tracking=True, store=True)
    prevous_school = fields.Char('Previous School')
    primary_language = fields.Char('Primary Language')
    second_language = fields.Char('Second Language')
    sibing_status = fields.Selection([('no_siblings', 'No Siblings'),('has_brothers_sisters', 'Brothers/Sisters in School'), ('staff_child', 'Staff Child')], default='no_siblings', string='Sibling Status')
    state = fields.Selection([('draft', 'Draft'), ('admitted', 'Admitted'), ('cancelled', 'Cancelled'),('inactive', 'Inactive'),('withdrawn', 'Withdrawn')], 'State', default='draft', tracking=True)
    date_of_apply = fields.Date('Admission Date', default=datetime.today())
    date_of_admission = fields.Datetime('Date of Admission')
    admitted_by = fields.Many2one('res.users', string='Admitted By')
    date_of_withdraw = fields.Datetime('Date Withdrawn')
    withdraw_by = fields.Many2one('res.users', string='Withdrawn By')
    
    family_id = fields.Many2one('student.parent.guardian.info', string="Family ID")
    
    # Fields (Father) 
    father_full_name = fields.Char('Father Full Name', tracking=True)
    father_full_name_arabic = fields.Char('Father Full Name Arabic')
    father_first_name = fields.Char('Father First Name', tracking=True)
    father_middle_name = fields.Char('Father Second Name')
    father_last_name = fields.Char('Father Third Name')
    father_fourth_name = fields.Char('Father Forth Name')
    father_passport = fields.Char('Father Passport No')

    father_first_name_arabic = fields.Char('Father First Name Arabic')
    father_middle_name_arabic = fields.Char('Father Second Name Arabic')
    father_last_name_arabic = fields.Char('Father Third Name Arabic')
    father_fourth_name_arabic = fields.Char('Father Forth Name Arabic')
    father_national_id = fields.Char('Father National ID', tracking=True)
    father_nationality = fields.Many2one('res.country', string='Father Nationality')
    father_marital_status = fields.Selection([('single', 'Single'), ('married', 'Married'), ('divorced', 'Divorced'), ('widow', 'Widow/widower')], string='Father Marital Status')
    father_degree_education = fields.Char('Father Education')
    father_employment = fields.Char('Father Employment')
    father_employer_location = fields.Char('Father Employment Location')
    father_landline_number = fields.Char('Father Home Phone')
    father_land_line_no = fields.Char('Father Work Phone')
    father_mobile_no = fields.Char('Father Mobile Number', tracking=True)
    father_email = fields.Char(string='Father Email')
    father_is_absent = fields.Boolean('Father is Absent')
    father_active_employee = fields.Boolean('Father Active Employee')
    
    # Fields(Mother)
    mother_full_name = fields.Char('Mother Full Name', tracking=True)
    mother_full_name_arabic = fields.Char('Mother Full Name Arabic')
    mother_first_name = fields.Char('Mother First Name')
    mother_middle_name = fields.Char('Mother Second Name')
    mother_last_name = fields.Char('Mother Third Name')
    mother_fourth_name = fields.Char('Mother Forth Name')
    mother_first_name_arabic = fields.Char('Mother First Name Arabic')
    mother_middle_name_arabic = fields.Char('Mother Second Name Arabic')
    mother_last_name_arabic = fields.Char('Mother Third Name Arabic')
    mother_fourth_name_arabic = fields.Char('Mother Forth Name Arabic')
    mother_passport = fields.Char('Mother Passport No')
    mother_national_id = fields.Char('Mother National ID', tracking=True)
    mother_nationality = fields.Many2one('res.country', string='Mother Nationality')
    mother_marital_status = fields.Selection([('single', 'Single'), ('married', 'Married'), ('divorced', 'Divorced'), ('widow', 'Widow/widower')], string='Mother Marital Status')
    mother_degree_education = fields.Char('Mother Education')
    mother_employment = fields.Char('Mother Employment')
    mother_employer_location = fields.Char('Mother Employment Location')
    mother_landline_number = fields.Char('Mother Home Phone')
    mother_land_line_no = fields.Char('Mother Work Phone')
    mother_mobile_no = fields.Char('Mother Mobile Number', tracking=True)
    mother_email = fields.Char(string='Mother Email')
    mother_is_absent = fields.Boolean('Mother is Absent')
    mother_active_employee = fields.Boolean('Mother Active Employee')

    # Guardian Fields:
    legal_guardian = fields.Selection([('father_is_legal_guardian', 'Father is the legal guardian'), ('mother_is_legal_guardian', 'Mother is the legal guardian'), ('other', 'Other')], string='Legal Guardian')
    guardian_full_name = fields.Char('Guardian Full Name', tracking=True)
    guardian_full_name_arabic = fields.Char('Guardian Full Name Arabic')
    guardian_first_name = fields.Char('Guardian First Name')
    guardian_middle_name = fields.Char('Guardian Second Name')
    guardian_last_name = fields.Char('Guardian Third Name')
    guardian_fourth_name = fields.Char('Guardian Forth Name')
    guardian_first_name_arabic = fields.Char('Guardian First Name Arabic')
    guardian_middle_name_arabic = fields.Char('Guardian Second Name Arabic')
    guardian_last_name_arabic = fields.Char('Guardian Third Name Arabic')
    guardian_fourth_name_arabic = fields.Char('Guardian Forth Name Arabic')
    guardian_passport = fields.Char('Guardian Passport No')
    guardian_national_id = fields.Char('Guardian National ID', tracking=True)
    relation_to_child = fields.Char('Relation to The Child')
    guardian_nationality = fields.Many2one('res.country', string='Guardian Nationality')
    guardian_marital_status = fields.Selection([('single', 'Single'), ('married', 'Married'), ('divorced', 'Divorced'), ('widow', 'Widow/widower')], string='Guardian Marital Status')
    guardian_degree_education = fields.Char('Guardian Education')
    guardian_employment = fields.Char('Guardian Employment')
    guardian_employeer_location = fields.Char('Guardian Employment Location')
    guardian_landline_number = fields.Char('Guardian Home Phone')
    guardian_land_line_no = fields.Char('Guardian Work Phone')
    guardian_mobile_no = fields.Char('Guardian Mobile Number', tracking=True)
    guardian_email = fields.Char(string='Guardian Email')
    student_class_ids = fields.One2many('student.class', 'student_id', string='Student Class')
    student_courses_ids = fields.One2many('student.courses', 'student_id', string='Student Courses')
    #moodle
    md_parent_username = fields.Char('Parent User Name')
    md_password = fields.Char('Password')
    md_username = fields.Char('User Name')
    mooddle_id = fields.Char('EduSync ID', tracking=True)
    moodle_status = fields.Selection([('active', 'Active'), ('in_active', 'In Active'), ('deleted', 'Deleted')], tracking=True, string='Moodle Status', default='active')
    reason = fields.Selection([('Fee_defaulter','Fee Defaulter'),('other','Other')],'Reason',default='Fee_defaulter')
    due_amount = fields.Float(compute='_due_month', string='Due Amount')
    fee_balance = fields.Float(compute='student_fee_balance', string='Fee Balance')
    due_month = fields.Char(compute='_due_month', string='Due Month')

    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)
    synced_with_lms = fields.Boolean('Synced with LMS', related='company_id.synced_with_lms', readonly=True)

    admitted_status = fields.Selection([('paid', 'Paid'), ('unpaid', 'Unpaid')], default='unpaid', compute='_compute_set_admitted', string='Admitted Status',store=True)
    student_admission_form_id = fields.Many2one('student.admission.form')

    @api.onchange('family_id')
    def _onchange_built_up(self):
        """
        This method will change the field's value when the dependend field's value changes.
        -----------------------------------------------------------------------------------
        @param self: object pointer
        """
        for student in self:
            student.father_full_name = student.family_id.father_full_name
            student.father_full_name_arabic = student.family_id.father_full_name_arabic
            student.father_first_name = student.family_id.father_first_name
            student.father_middle_name = student.family_id.father_middle_name
            student.father_last_name = student.family_id.father_last_name
            student.father_fourth_name = student.family_id.father_fourth_name
            student.father_passport = student.family_id.father_passport
            student.father_first_name_arabic = student.family_id.father_first_name_arabic
            student.father_middle_name_arabic = student.family_id.father_middle_name_arabic
            student.father_last_name_arabic = student.family_id.father_last_name_arabic
            student.father_fourth_name_arabic = student.family_id.father_fourth_name_arabic
            student.father_is_absent = student.family_id.father_is_absent
            student.father_email = student.family_id.father_email
            student.father_mobile_no = student.family_id.father_mobile_no
            student.father_land_line_no = student.family_id.father_land_line_no
            student.father_employer_location = student.family_id.father_employer_location
            student.father_employment = student.family_id.father_employment
            student.father_national_id = student.family_id.father_national_id
            student.father_nationality = student.family_id.father_nationality
            student.father_marital_status = student.family_id.father_marital_status
            student.father_degree_education = student.family_id.father_degree_education
            student.father_landline_number = student.family_id.father_landline_number

            student.mother_full_name = student.family_id.mother_full_name
            student.mother_full_name_arabic = student.family_id.mother_full_name_arabic
            student.mother_first_name = student.family_id.mother_first_name
            student.mother_middle_name = student.family_id.mother_middle_name
            student.mother_last_name = student.family_id.mother_last_name
            student.mother_fourth_name = student.family_id.mother_fourth_name
            student.mother_passport = student.family_id.mother_passport
            student.mother_first_name_arabic = student.family_id.mother_first_name_arabic
            student.mother_middle_name_arabic = student.family_id.mother_middle_name_arabic
            student.mother_last_name_arabic = student.family_id.mother_last_name_arabic
            student.mother_fourth_name_arabic = student.family_id.mother_fourth_name_arabic
            student.mother_is_absent = student.family_id.mother_is_absent
            student.mother_email = student.family_id.mother_email
            student.mother_mobile_no = student.family_id.mother_mobile_no
            student.mother_land_line_no = student.family_id.mother_land_line_no
            student.mother_employer_location = student.family_id.mother_employer_location
            student.mother_employment = student.family_id.mother_employment
            student.mother_national_id = student.family_id.mother_national_id
            student.mother_nationality = student.family_id.mother_nationality
            student.mother_marital_status = student.family_id.mother_marital_status
            student.mother_degree_education = student.family_id.mother_degree_education
            student.mother_landline_number = student.family_id.mother_landline_number

            student.legal_guardian = student.family_id.legal_guardian
            student.guardian_full_name = student.family_id.guardian_full_name
            student.guardian_first_name = student.family_id.guardian_first_name
            student.guardian_middle_name = student.family_id.guardian_middle_name
            student.guardian_last_name = student.family_id.guardian_last_name
            student.guardian_fourth_name = student.family_id.guardian_fourth_name
            student.guardian_passport = student.family_id.guardian_passport
            student.guardian_first_name_arabic = student.family_id.guardian_first_name_arabic
            student.guardian_middle_name_arabic = student.family_id.guardian_middle_name_arabic
            student.guardian_last_name_arabic = student.family_id.guardian_last_name_arabic
            student.guardian_fourth_name_arabic = student.family_id.guardian_fourth_name_arabic
            student.guardian_email = student.family_id.guardian_email
            student.guardian_mobile_no = student.family_id.guardian_mobile_no
            student.guardian_land_line_no = student.family_id.guardian_land_line_no
            student.guardian_employment = student.family_id.guardian_employment
            student.guardian_national_id = student.family_id.guardian_national_id
            student.guardian_nationality = student.family_id.guardian_nationality
            student.guardian_marital_status = student.family_id.guardian_marital_status
            student.guardian_degree_education = student.family_id.guardian_degree_education
            student.guardian_landline_number = student.family_id.guardian_landline_number


    def student_fee_balance(self):
        """
        Call this central method whenever you need to findout total outstanding dues not paid 
        by student, may be this method is more enhanced in future...
        
        """
        for student in self:
            _sql = """SELECT  COALESCE(sum(total_amount),'0')  FROM student_fee
                      WHERE student_id = """+str(student.id)+ """ AND status = 'unpaid' """  
            self.env.cr.execute(_sql)
            amount = self.env.cr.fetchone()[0]
            self.fee_balance = amount
        
    def _due_month(self):
        today = fields.Date.today()
        std_fee = self.env['student.fee'].search([('student_id','=',self.id),('status','=','unpaid'),('due_date','>',today)])
        smaller_duedate = '00-00-0000'
        smaller_amount = 0.0
        if std_fee:
            smaller_duedate = std_fee[-1].due_date 
            
            smaller_amount = std_fee[-1].applied_fee
            if smaller_duedate:
                smaller_duedate =str(datetime.strptime(str(smaller_duedate), '%Y-%m-%d').strftime('%d-%b-%Y'))
        
        self.due_month = smaller_duedate
        self.due_amount = smaller_amount
        return
    
        
    def action_dues_student_fee(self):
        
        today = datetime.now()
        std_fee = self.env['student.fee'].search([('student_id','=',self.env.context.get('std_id')),('status','=','unpaid'),('due_date','>',today)])
        if std_fee:
            std_fee =std_fee[0]
        return {
            'name':'Student Fee',
            'view_type': 'form',
            'view_mode': 'tree',
            'view_id': self.env.ref('sms_core.sms_core_fee_student_fee_tree').id,
            'res_model': 'student.fee',
            'type': 'ir.actions.act_window',
            'target': 'new',
             'domain': "[('id', '=', %s)]" % std_fee.id,
            }
    def write(self, vals):
        """
        Overridden write method to update the family record of student
        Also to check the lms integration and update user on lms.
        --------------------------------------------------------------
        :param vals: A dictionary containing fields and values
        :return: True
        """
        family_obj = self.env['student.parent.guardian.info']
        for student in self:
            if not student._context.get('parent_creation'):
                student_family_dict = student.student_family_prepare(vals)
                domain = []
                if vals.get('father_national_id') or student.father_national_id:
                    domain.append(('father_national_id', '=', vals.get('father_national_id') or student.father_national_id))
                elif vals.get('mother_national_id') or student.mother_national_id:
                    domain.append(('mother_national_id', '=', vals.get('mother_national_id') or student.mother_national_id))
                elif vals.get('father_passport') or student.father_passport:
                    domain.append(('father_passport', '=', vals.get('father_passport') or student.father_passport))
                elif vals.get('mother_passport') or student.mother_passport:
                    domain.append(('mother_passport', '=', vals.get('mother_passport') or student.mother_passport))
                elif vals.get('guardian_national_id') or student.guardian_national_id:
                    domain.append(('guardian_national_id', '=', vals.get('guardian_national_id') or student.guardian_national_id))
                elif vals.get('guardian_passport') or student.guardian_passport:
                    domain.append(('guardian_passport', '=', vals.get('guardian_passport') or student.guardian_passport))
                family_rec = family_obj.search(domain, limit=1)
                if family_rec.ids:
                    self.with_context(parent_creation=True).write({'family_id': family_rec.id})
                    family_rec.write(student_family_dict)
                else:
                    new_family_id = self.env['student.parent.guardian.info'].create(student_family_dict)
                    self.with_context(parent_creation=True).write({'family_id': new_family_id.id})
        res = super(AcademicStudent, self).write(vals)
        for student in self:
            if 'full_name' in vals:
                full_name = student.full_name.split()
                first_name = full_name[0]
                last_name = ' '
                if len(full_name) > 1:
                     last_name = full_name[1]
                try:
                    if self.env.company.synced_with_lms:
                        parameters = '&users[0][id]=' + str(student.mooddle_id) + '&users[0][username]=' + str(student.md_username) + '&users[0][firstname]=' + str(first_name)+ '&users[0][lastname]=' + str(last_name)+ '&users[0][password]=' + str(student.md_password)
                        moodle_url = 'http://'+self.env.company.lms_url+'/webservice/rest/server.php' + '?wstoken=' + self.env.company.lms_url_token + parameters + '&wsfunction=core_user_update_users&moodlewsrestformat=json'
                        head_params = {'wsfunction': 'core_user_update_users', 'moodlewsrestformat': 'json'}
                        response = requests.get(moodle_url, params=head_params)
                        response = response.json()
                        print("User update on LMS response", response)
                except:
                    raise UserError(_('Record not updated on lms contact your system administrator'))
        return res

    @api.model
    def create(self, vals):
        """
        Overridden create method to create a partner for the student and link it to the student.
        check the family information and either link it to the family record or create one.
        ----------------------------------------------------------------------------------------
        :param vals: A dictionary containing fields and values
        :return: a record set of the newly created record
        """
        family_obj = self.env['student.parent.guardian.info']
        res = super(AcademicStudent, self.with_context(parent_creation=True)).create(vals)
        partner = self.env['res.partner'].create({'name': res.full_name})
        res.partner_id = partner.id
        student_family_dict = res.student_family_prepare(vals)
        domain = []
        if res.father_national_id:
            domain.append(('father_national_id','=',res.father_national_id))
        elif res.father_passport:
            domain.append(('father_passport', '=', res.father_passport))
        elif res.mother_national_id:
            domain.append(('mother_national_id', '=', res.mother_national_id))
        elif res.mother_passport:
            domain.append(('mother_passport', '=', res.mother_passport))
        elif res.guardian_national_id:
            domain.append(('guardian_national_id', '=', res.guardian_national_id))
        elif res.guardian_passport:
            domain.append(('guardian_passport', '=', res.guardian_passport))
        family_rec = family_obj.search(domain, limit=1)
        if family_rec.ids:
            res.family_id = family_rec.id
            family_rec.write(student_family_dict)
        else:
            new_family_id = family_obj.create(student_family_dict)
            res.family_id = new_family_id.id
        return res

    @api.depends('student_fee_ids', 'student_fee_ids.status')
    def _compute_set_admitted(self):
        payment_status = ''
        for res in self:
            for line in res.student_fee_ids:
                if line.status == 'paid' or payment_status == 'paid':
                    payment_status = line.status
                    res.admitted_status = 'paid'
                else:
                    res.admitted_status = 'unpaid'

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """
        Overridden name_search method to search based on name and code
        --------------------------------------------------------------
        :param self: object pointer
        :param name: the string typed in for searching the name
        :param args: the domain passed on the field
        :param operator: default is ilike so can search the matching string
        :param limit: max no of records
        """
        dom = ['|', '|', '|', '|', '|', '|', '|', '|', '|',
               ('first_name', operator, name), ('middle_name', operator, name),
               ('second_middle_name', operator, name), ('last_name', operator, name),
               ('full_name', operator, name), ('full_name_arabic', operator, name),
               ('first_name_arabic', operator, name), ('middle_name_arabic', operator, name),
               ('second_middle_name_arabic', operator, name), ('last_name_arabic', operator, name)]
        if args:
            dom += args
        student_name = self.search(dom, limit=limit)
        return student_name.name_get()

    def student_family_prepare(self, vals):

        student_family_dict = {
            # father
            'father_full_name': vals.get('father_full_name') or self.father_full_name,
            'father_first_name': vals.get('father_first_name') or self.father_first_name,
            'father_middle_name': vals.get('father_middle_name') or self.father_middle_name,
            'father_last_name': vals.get('father_last_name') or self.father_last_name,
            'father_fourth_name': vals.get('father_fourth_name') or self.father_fourth_name,
            'father_full_name_arabic': vals.get('father_full_name_arabic') or self.father_full_name_arabic,
            'father_first_name_arabic': vals.get('father_first_name_arabic') or self.father_first_name_arabic,
            'father_middle_name_arabic': vals.get('father_middle_name_arabic') or self.father_middle_name_arabic,
            'father_last_name_arabic': vals.get('father_last_name_arabic') or self.father_last_name_arabic,
            'father_fourth_name_arabic': vals.get('father_fourth_name_arabic') or self.father_fourth_name_arabic,
            'father_national_id': vals.get('father_national_id') or self.father_national_id,
            'father_passport': vals.get('father_passport') or self.father_passport,
            'father_nationality': vals.get('father_nationality') or self.father_nationality.id,
            'father_marital_status': vals.get('father_marital_status') or self.father_marital_status,
            'father_degree_education': vals.get('father_degree_education') or self.father_degree_education,
            'father_employment': vals.get('father_employment') or self.father_employment,
            'father_employer_location': vals.get('father_employer_location') or self.father_employer_location,
            'father_landline_number': vals.get('father_landline_number') or self.father_landline_number,
            'father_land_line_no': vals.get('father_land_line_no') or self.father_land_line_no,
            'father_mobile_no': vals.get('father_mobile_no') or self.father_mobile_no,
            'father_email': vals.get('father_email') or self.father_email,
            'father_is_absent': vals.get('father_is_absent') or self.father_is_absent,

            # mother
            'mother_full_name': vals.get('mother_full_name') or self.mother_full_name,
            'mother_first_name': vals.get('mother_first_name') or self.mother_first_name,
            'mother_middle_name': vals.get('mother_middle_name') or self.mother_middle_name,
            'mother_last_name': vals.get('mother_last_name') or self.mother_last_name,
            'mother_fourth_name': vals.get('mother_fourth_name') or self.mother_fourth_name,
            'mother_full_name_arabic': vals.get('mother_full_name_arabic') or self.mother_full_name_arabic,
            'mother_first_name_arabic': vals.get('mother_first_name_arabic') or self.mother_first_name_arabic,
            'mother_middle_name_arabic': vals.get('mother_middle_name_arabic') or self.mother_middle_name_arabic,
            'mother_last_name_arabic': vals.get('mother_last_name_arabic') or self.mother_last_name_arabic,
            'mother_fourth_name_arabic': vals.get('mother_fourth_name_arabic') or self.mother_fourth_name_arabic,
            'mother_national_id': vals.get('mother_national_id') or self.mother_national_id,
            'mother_passport': vals.get('mother_passport') or self.mother_passport,
            'mother_nationality': vals.get('mother_nationality') or self.mother_nationality.id,
            'mother_marital_status': vals.get('mother_marital_status') or self.mother_marital_status,
            'mother_degree_education': vals.get('mother_degree_education') or self.mother_degree_education,
            'mother_employment': vals.get('mother_employment') or self.mother_employment,
            'mother_employer_location': vals.get('mother_employer_location') or self.mother_employer_location,
            'mother_landline_number':vals.get('mother_landline_number') or self.mother_landline_number,
            'mother_land_line_no': vals.get('mother_land_line_no') or self.mother_land_line_no,
            'mother_mobile_no': vals.get('mother_mobile_no') or self.mother_mobile_no,
            'mother_email': vals.get('mother_email') or self.mother_email,
            'mother_is_absent':vals.get('mother_is_absent') or self.mother_is_absent,
            # Guardian
            'legal_guardian': vals.get('legal_guardian') or self.legal_guardian,
            'guardian_full_name': vals.get('guardian_full_name') or self.guardian_full_name,
            'guardian_first_name': vals.get('guardian_first_name') or self.guardian_first_name,
            'guardian_middle_name': vals.get('guardian_middle_name') or self.guardian_middle_name,
            'guardian_last_name': vals.get('guardian_last_name') or self.guardian_last_name,
            'guardian_fourth_name': vals.get('guardian_fourth_name') or self.guardian_fourth_name,
            'guardian_full_name_arabic': vals.get('guardian_full_name_arabic') or self.guardian_full_name_arabic,
            'guardian_first_name_arabic': vals.get('guardian_first_name_arabic') or self.guardian_first_name_arabic,
            'guardian_middle_name_arabic': vals.get('guardian_middle_name_arabic') or self.guardian_middle_name_arabic,
            'guardian_last_name_arabic': vals.get('guardian_last_name_arabic') or self.guardian_last_name_arabic,
            'guardian_fourth_name_arabic': vals.get('guardian_fourth_name_arabic') or self.guardian_fourth_name_arabic,
            'guardian_national_id': vals.get('guardian_national_id') or self.guardian_national_id,
            'guardian_passport': vals.get('guardian_passport') or self.guardian_passport,
            'guardian_nationality': vals.get('guardian_nationality') or self.guardian_nationality,
            'guardian_marital_status': vals.get('guardian_marital_status') or self.guardian_marital_status,
            'relation_to_child': vals.get('relation_to_child') or self.relation_to_child,
            'guardian_degree_education': vals.get('guardian_degree_education') or self.guardian_degree_education,
            'guardian_employment': vals.get('guardian_employment') or self.guardian_employment,
            'guardian_employeer_location': vals.get('guardian_employeer_location') or self.guardian_employeer_location,
            'guardian_landline_number': vals.get('guardian_landline_number') or self.guardian_landline_number,
            'guardian_land_line_no': vals.get('guardian_land_line_no') or self.guardian_land_line_no,
            'guardian_mobile_no': vals.get('guardian_mobile_no') or self.guardian_mobile_no,
            'guardian_email': vals.get('guardian_email') or self.guardian_email,
        }
        return student_family_dict




class StudentClass(models.Model):
    _name = "student.class"
    _description = "student.class"
    
    def unlink(self):
        if self.status != 'draft':
            raise UserError(_('Record can only be deleted in Draft State.'))
        else:
            rec = super(StudentClass, self).unlink()    
        return rec
    
    student_id = fields.Many2one('academic.student', string='Student')
    class_id = fields.Many2one('school.class', string='Class')
    class_section_id = fields.Many2one('class.section', string='Section', tracking=True)
    std_course_ids = fields.One2many('student.courses', 'std_class_id', string='Courses')
    status = fields.Selection([('draft', 'Draft'), ('active', 'Active'), ('closed', 'Closed'), ('withdrawn', 'Withdrawn')], string='Status')
    
    @api.model
    def create(self, vals):
        class_obj = super(StudentClass, self).create(vals)
        try:
            if self.env.company.synced_with_lms:
                parameters = '&members[0][cohorttype][type]=id'+\
                             '&members[0][cohorttype][value]='+str(class_obj.class_section_id.mooddle_id)+\
                             '&members[0][usertype][type]=id'+\
                             '&members[0][usertype][value]='+str(class_obj.student_id.mooddle_id)

                moodle_url = 'http://'+self.env.company.lms_url+'/webservice/rest/server.php' + '?wstoken=' + self.env.company.lms_url_token + parameters + '&wsfunction=core_cohort_add_cohort_members&moodlewsrestformat=json'
                head_params = {'wsfunction':'core_cohort_add_cohort_members', 'moodlewsrestformat':'json'}
                response = requests.get(moodle_url, params=head_params)
                response = response.json()
        except:
            raise UserError(_('Record not added on lms contact your system administrator'))
            
        print("this is object ----> ", class_obj)
        course_obj = self.env['class.course'].search([('class_id', '=', class_obj.class_id.id), ('active', '=', True)])
        print("Course object ----> ", course_obj)
        for f in course_obj:
            print("inside for loop ----> ", f)
            self.env['student.courses'].create({
                    'student_id': class_obj.student_id.id,
                    'class_id': class_obj.class_id.id,
                    'class_course_id':f.id,
                    'std_class_id': class_obj.id,
                    'course_status':'active',
                    })
        return class_obj
    
class StudentCourses(models.Model):
    _name = "student.courses"
    _description = "student.courses"
    
    def unlink(self):
        if self.course_status != 'draft':
            raise UserError(_('Record can only be deleted in Draft State.'))
        else:
            rec = super(StudentCourses, self).unlink()    
        return rec
    
    
    student_id = fields.Many2one('academic.student', string='Student')
    class_id = fields.Many2one('school.class', string='Class')
    class_course_id = fields.Many2one('class.course', string='Class Course')
    std_class_id = fields.Many2one('student.class', string='Student Class')
    course_status = fields.Selection([('draft', 'Draft'), ('active', 'Active'), ('closed', 'Closed'), ('withdrawn', 'Withdrawn')], string='Status')
    
    @api.model
    def create(self, vals):
        std_cur_obj = super(StudentCourses, self).create(vals)
        
#         if not std_cur_obj.student_id.mooddle_id or std_cur_obj.class_course_id.mooddle_id:
#             raise UserError(_('%s') % ("Empty Parameter list"))
#         print("student_id.mooddle_id....",std_cur_obj.student_id.mooddle_id)
#         print("" ,std_cur_obj.class_course_id.mooddle_id)
#         
#         course_moodle_id = std_cur_obj.class_course_id.mooddle_id
#         user_moodle_id = std_cur_obj.student_id.mooddle_id
#         if not course_moodle_id:
#             raise UserError(_('The Course '+str(std_cur_obj.class_course_id.name)+' is not available on Moodle. Synch the course before proceeding'))
#         
#         if not user_moodle_id:
#             raise UserError(_('The User '+str(std_cur_obj.student_id.full_name)+' is not available on Moodle. Synch the course before proceeding'))
#         parameters= '&enrolments[0][roleid]=5&enrolments[0][userid]='+str(int(user_moodle_id))+'&enrolments[0][courseid]='+str(int(course_moodle_id))
#         print("print before ",parameters)
#         moodle_url = 'http://35.192.148.38/webservice/rest/server.php?wstoken=ff5b4be8d6383ff175a5522805583246'+parameters+'&wsfunction=enrol_manual_enrol_users&moodlewsrestformat=json'
#         head_params = {'wsfunction':'enrol_manual_enrol_users', 'moodlewsrestformat':'json'}
#         response = requests.get(moodle_url, params=head_params)
#         response = response.json()
#         print("response--------",response)
# #         if response['errorcode']:
#             raise UserError(_('%s') % (response['errorcode']))
#         print("******course response std creation response",response)
        return std_cur_obj
    
    
class StudentParentGuardianInfo(models.Model):
    _name = 'student.parent.guardian.info'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'student.parent.guardian.info'
    
    def _set_name(self):
        for f in self:
            if not f.father_is_absent:
                f.head_person = 'father'
            elif not f.mother_is_absent:
                f.head_person = 'mother'
            else:
                f.head_person = 'guardian'
            if f.student_ids and len(f.student_ids) > 0:
                f.name = f.student_ids[0].full_name
                f.name_arabic = f.student_ids[0].full_name_arabic
        return

    @api.constrains('father_mobile_no')
    def check_father_mobile_no(self):
        """
        This will check phone number is must be in format
        -------------------------------------------------
        @param self: object pointer
        """
        for guardian in self:
            if not guardian.father_is_absent and guardian.father_mobile_no:
                pattern = re.compile('^(\+20){1}[0-9]{8,10}$')
                father_no_check = pattern.match(guardian.father_mobile_no)
                if father_no_check is None:
                    raise ValidationError(_('Please Enter a Father Valid Phone No! For e.g. +20xxxxxx'))

    @api.constrains('mother_mobile_no')
    def check_mother_mobile_no(self):
        """
        This will check phone number is must be in format
        -------------------------------------------------
        @param self: object pointer
        """
        for guardian in self:
            if not guardian.mother_is_absent and guardian.mother_mobile_no:
                pattern = re.compile('^(\+20){1}[0-9]{8,10}$')
                mother_no_check = pattern.match(guardian.mother_mobile_no)
                if mother_no_check is None:
                    raise ValidationError(_('Please Enter a Mother Valid Phone No! For e.g. +20xxxxxx'))

    @api.constrains('guardian_mobile_no')
    def check_guardian_mobile_no(self):
        """
        This will check phone number is must be in format
        -------------------------------------------------
        @param self: object pointer
        """
        for guardian in self:
            if guardian.legal_guardian == 'other' and guardian.guardian_mobile_no:
                pattern = re.compile('^(\+20){1}[0-9]{8,10}$')
                guardian_no_check = pattern.match(guardian.guardian_mobile_no)
                if guardian_no_check is None:
                    raise ValidationError(_('Please Enter a Guardian Valid Phone No! For e.g. +20xxxxxx'))

    name = fields.Char(compute='_set_name', string='Student Name', tracking=True)
    name_arabic = fields.Char(compute='_set_name', string='Student Name Arabic', tracking=True, store=True)
    head_person = fields.Selection([('father', 'Father is Contact Head'), ('mother', 'Mother is Contact Head'), ('guardian', 'Guardian is Contact Head')], string='Head Person')
    student_ids = fields.One2many('academic.student','family_id', string='Childs')
    # Fields (Father) 
    father_full_name = fields.Char('Father Full Name', tracking=True)
    father_first_name = fields.Char('Father First Name', tracking=True)
    father_middle_name = fields.Char('Father Second Name')
    father_last_name = fields.Char('Father Third Name')
    father_fourth_name = fields.Char('Father Forth Name')
    father_passport = fields.Char('Passport No')

    father_first_name_arabic = fields.Char('Father First Name Arabic')
    father_middle_name_arabic = fields.Char('Father Second Name Arabic')
    father_last_name_arabic = fields.Char('Father Third Name Arabic')
    father_fourth_name_arabic = fields.Char('Father Forth Name Arabic')
    father_full_name_arabic = fields.Char('Father Full Name Arabic', tracking=True)
    father_national_id = fields.Char('National ID', tracking=True)
    father_nationality = fields.Many2one('res.country', string='Nationality')
    father_marital_status = fields.Selection([('single', 'Single'), ('married', 'Married'), ('divorced', 'Divorced'), ('widow', 'Widow/widower')], string='Marital Status')
    father_degree_education = fields.Char('Education')
    father_employment = fields.Char('Employment')
    father_employer_location = fields.Char('Employment Location')
    father_landline_number = fields.Char('Home Phone')
    father_land_line_no = fields.Char('Work Phone')
    father_mobile_no = fields.Char('Mobile Number', tracking=True)
    father_email = fields.Char(string='Email')
    father_is_absent = fields.Boolean('Father is Absent')
    
    # Fields(Mother)
    mother_full_name = fields.Char('Mother Full Name', tracking=True)
    mother_full_name_arabic = fields.Char('Mother Full Name Arabic', tracking=True)
    mother_first_name = fields.Char('Mother First Name')
    mother_middle_name = fields.Char('Mother Second Name')
    mother_last_name = fields.Char('Mother Third Name')
    mother_fourth_name = fields.Char('Mother Forth Name')
    mother_first_name_arabic = fields.Char('Mother First Name Arabic')
    mother_middle_name_arabic = fields.Char('Mother Second Name Arabic')
    mother_last_name_arabic = fields.Char('Mother Third Name Arabic')
    mother_fourth_name_arabic = fields.Char('Mother Forth Name Arabic')
    mother_passport = fields.Char('Passport No')
    mother_national_id = fields.Char('National ID', tracking=True)
    mother_nationality = fields.Many2one('res.country', string='Nationality')
    mother_marital_status = fields.Selection([('single', 'Single'), ('married', 'Married'), ('divorced', 'Divorced'), ('widow', 'Widow/widower')], string='Marital Status')
    mother_degree_education = fields.Char('Education')
    mother_employment = fields.Char('Employment')
    mother_employer_location = fields.Char('Employment Location')
    mother_landline_number = fields.Char('Home Phone')
    mother_land_line_no = fields.Char('Work Phone')
    mother_mobile_no = fields.Char('Mobile Number', tracking=True)
    mother_email = fields.Char(string='Email')
    mother_is_absent = fields.Boolean('Mother is Absent')
    
    # Guardian Fields:
    legal_guardian = fields.Selection([('father_is_legal_guardian', 'Father is the legal guardian'), ('mother_is_legal_guardian', 'Mother is the legal guardian'), ('other', 'Other')], string='Legal Guardian')
    guardian_full_name = fields.Char('Guardian Full Name', tracking=True)
    guardian_full_name_arabic = fields.Char('Guardian Full Name Arabic', tracking=True)
    guardian_first_name = fields.Char('Guardian First Name')
    guardian_middle_name = fields.Char('Guardian Second Name')
    guardian_last_name = fields.Char('Guardian Third Name')
    guardian_fourth_name = fields.Char('Guardian Forth Name')
    guardian_first_name_arabic = fields.Char('Guardian First Name Arabic')
    guardian_middle_name_arabic = fields.Char('Guardian Second Name Arabic')
    guardian_last_name_arabic = fields.Char('Guardian Third Name Arabic')
    guardian_fourth_name_arabic = fields.Char('Guardian Forth Name Arabic')
    guardian_passport = fields.Char('Passport No')
    guardian_national_id = fields.Char('National ID', tracking=True)
    relation_to_child = fields.Char('Relation to The Child')
    guardian_nationality = fields.Many2one('res.country', string='Nationality')
    guardian_marital_status = fields.Selection([('single', 'Single'), ('married', 'Married'), ('divorced', 'Divorced'), ('widow', 'Widow/widower')], string='Marital Status')
    guardian_degree_education = fields.Char('Education')
    guardian_employment = fields.Char('Employment')
    guardian_employeer_location = fields.Char('Employment Location')
    guardian_landline_number = fields.Char('Home Phone')
    guardian_land_line_no = fields.Char('Work Phone')
    guardian_mobile_no = fields.Char('Mobile Number', tracking=True)
    guardian_email = fields.Char(string='Email')

    
      
    
