# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#
##############################################################################
import base64
import PyPDF2
from tempfile import gettempdir
import os

from odoo import models, fields, api, _, tools
from odoo.exceptions import ValidationError
import re
from odoo.tools import ustr


class Applicant(models.Model):
    _inherit = 'hr.applicant'

    @api.depends('partner_name', 'middle_name', 'last_name', 'fourth_name')
    def _compute_name(self):
        for emp in self:
            emp.full_name = "%s %s %s %s" %(ustr(emp.partner_name or ""), ustr(emp.middle_name or ""), ustr(emp.last_name or ""), ustr(emp.fourth_name or ""))

    @api.depends('first_name_arabic', 'middle_name_arabic', 'last_name_arabic', 'fourth_name_arabic')
    def _compute_employee_name_arabic(self):
        for emp in self:
            emp.full_name_arabic = str(emp.first_name_arabic) + " " + str(emp.middle_name_arabic) + " " + str(emp.last_name_arabic) + " " + str(emp.fourth_name_arabic)
    # Personal Data
    full_name = fields.Char('Name', compute="_compute_name", store=True, tracking=True)
    full_name_arabic = fields.Char('Name (Arabic)', compute="_compute_employee_name_arabic", store=True, tracking=True)
    first_name_arabic = fields.Char('First Name (Arabic)')
    middle_name_arabic = fields.Char('Second Name (Arabic)')
    last_name_arabic = fields.Char('Third Name (Arabic)')
    fourth_name_arabic = fields.Char('Fourth Name (Arabic)')
    middle_name = fields.Char('Second Name')
    last_name = fields.Char('Third Name')
    fourth_name = fields.Char('Fourth Name')
    religion = fields.Char('Religion')
    date_of_birth = fields.Date('Date of Birth')
    place_of_birth = fields.Many2one('res.country.state', 'Place of Birth')
    nationality_id = fields.Many2one('res.country', 'Nationality')
    gender = fields.Selection([('male', 'Male'),
                               ('female', 'Female')], 'Gender')
    national_id = fields.Char('National ID', size=14)
    passport_id = fields.Char('Passport No', tracking=True)
    marital_status = fields.Selection([('unmarried', 'Unmarried'),
                                       ('married', 'Married'),
                                       ('divorced', 'Divorced'),
                                       ('widowed', 'Widowed')], 'Marital Status')
    address = fields.Text('Address')
    city_id = fields.Many2one('res.city', 'City')
    state_id = fields.Many2one('res.country.state', 'State', related='city_id.state_id', store=True)
    country_id = fields.Many2one('res.country', 'Country', related='state_id.country_id', store=True)
    military_status = fields.Selection([('done', 'Done'),
                                        ('relieved', 'Relieved'),
                                        ('uncharged', 'Uncharged')], 'Military Status')
    general_service_status = fields.Selection([('done', 'Done'),
                                               ('relieved', 'Relieved'),
                                               ('uncharged', 'Uncharged')], 'General Service Status')

    # Family Information
    spouse_name = fields.Char('Partner Full Name')
    spouse_national_id = fields.Char('Partner National ID', size=14)
    spouse_academic_qualification = fields.Char('Partner Academic Qualification')
    spouse_date_of_birth = fields.Date('Partner Date of Birth')
    spouse_place_of_birth = fields.Many2one('res.country.state', 'Partner Place of Birth')
    spouse_employment = fields.Char('Partner Employment')
    spouse_employment_location = fields.Char('Partner Employment Location')
    spouse_with_children = fields.Boolean('With Children?')

    # Training & Experience
    training_ids = fields.One2many('hr.training', 'applicant_id', 'Training')
    experience_ids = fields.One2many('hr.experience', 'applicant_id', 'Experience')
    education_ids = fields.One2many('hr.education', 'applicant_id', 'Education')

    # Status
    state = fields.Selection([('draft', 'In Review'),
                              ('pending_for_interview', 'Pending for Interview'),
                              ('accepted', 'Accepted'),
                              ('canceled', 'Canceled'),
                              ('rejected', 'Rejected'),
                              ('closed', 'Closed')], 'Status',
                             tracking=True,
                             default='draft',
                             group_expand='_expand_states')

    # CV
    cv = fields.Binary('CV')
    fname = fields.Char('File Name')

    manager_id = fields.Many2one('hr.employee', 'Direct Manager')
    child_ids = fields.Many2many('hr.employee', string='Subordinates')
    working_schedule_id = fields.Many2one('resource.calendar', 'Working Schedule')
    starting_date = fields.Date('Starting Date')
    salary = fields.Float('Salary')
    annual_bonus = fields.Float('Annual Bonus')
    next_salary_date = fields.Date('Next Salary Date')
    addition_rate = fields.Float('Addition Rate')
    penalty_rate = fields.Float('Penalty Rate')

    @api.constrains('company_id')
    def check_company_email(self):
        """
        This method will check company email is configure or not
        --------------------------------------------------------
        @param self: object pointer
        """
        for applicant in self:
            if not applicant.company_id.email:
                raise ValidationError(_('Please configure email in Company!!!'))

    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).state.selection]

    @api.model_create_multi
    def create(self, vals_lst):
        """
        Overridden create method to set the applicant subject
        -----------------------------------------------------
        @param self: object pointer
        @param vals_lst: List of dictionary containing fields and values
        :return: Recordset of newly created record
        """
        for vals in vals_lst:
            vals['name'] = vals.get('partner_name') or '/'
        return super(Applicant, self).create(vals_lst)

    @api.constrains('national_id', 'passport_id')
    def check_national_id_passport_id(self):
        """
        This method will check national id or passport id fill or not
        and also check if national id fill then it must have 14 digits
        ---------------------------------------------------------------
        @param self: object pointer
        """
        for applicant in self:
            if not applicant.national_id and not applicant.passport_id:
                raise ValidationError(_('Please Fill Either National ID or Passport No'))

            if applicant.national_id:
                if len(self.national_id) != 14 or not self.national_id.isdigit():
                    raise ValidationError(_('National Id must be 14 digits!'))

    @api.constrains('spouse_national_id')
    def check_spouse_national_id(self):
        """
        This will check national id must have 14 digits(for partner)
        ------------------------------------------------------------
        @param self: object pointer
        """
        if self.spouse_national_id and (len(self.spouse_national_id) != 14 or not self.spouse_national_id.isdigit()):
            raise ValidationError(_('Partner National Id must be 14 digits!'))

    @api.constrains('partner_phone')
    def check_partner_phone(self):
        """
        This will check phone number is must be in format
        -------------------------------------------------
        @param self: object pointer
        """
        for applicant in self:
            if applicant.partner_phone:
                pattern = re.compile('^(\+20){1}[0-9]{8,10}$')
                check = pattern.match(applicant.partner_phone)
                if check is None:
                    raise ValidationError(_('Please Enter a Valid Phone No! For e.g. +20xxxxxx'))

    def ask_for_document(self):
        """
        This method will move the state of the applicant to Close
        And Create a employee of current applicant
        ----------------------------------------------------------
        @param self: object pointer
        """
        for applicant in self:
            employee = self.env['hr.employee']
            vals = {
                'job_id': self.job_id.id,
                'department_id': self.department_id.id,
                'parent_id': self.manager_id.id,
                'child_ids': [(6, 0, self.child_ids.ids)],
                'resource_calendar_id': self.working_schedule_id.id,
                'salary': self.salary,
                'starting_date': self.starting_date,
                'annual_bonus': self.annual_bonus,
                'name': self.partner_name,
                'first_name_arabic': self.first_name_arabic,
                'middle_name_arabic': self.middle_name_arabic,
                'last_name_arabic': self.last_name_arabic,
                'fourth_name_arabic': self.fourth_name_arabic,
                'middle_name': self.middle_name,
                'last_name': self.last_name,
                'fourth_name': self.fourth_name,
                'religion': self.religion,
                'birthday': self.date_of_birth,
                'birth_place': self.place_of_birth.id,
                'country_id': self.nationality_id.id,
                'gender_rec': self.gender,
                'national_id': self.national_id,
                'passport_id': self.passport_id,
                'marital_status': self.marital_status,
                'address_rec': self.address,
                'city_id': self.city_id.id,
                'phone_number': self.partner_phone,
                'military_status': self.military_status,
                'general_service_status': self.general_service_status,
                'emp_email': self.email_from,
                'work_email': self.partner_name.replace(' ', '.').lower() + '.' + self.fourth_name.replace(' ', '.').lower() + '@' + self.company_id.email.split('@')[1],
                'spouse_complete_name': self.spouse_name,
                'spouse_national_id': self.spouse_national_id,
                'spouse_academic_qualification': self.spouse_academic_qualification,
                'spouse_birthdate': self.spouse_date_of_birth,
                'spouse_place_of_birth': self.spouse_place_of_birth.id,
                'spouse_employment': self.spouse_employment,
                'spouse_employment_location': self.spouse_employment_location,
                'spouse_with_children': self.spouse_with_children,
                'next_salary_date': self.next_salary_date,
                'addition_rate': self.addition_rate,
                'penalty_rate': self.penalty_rate,
            }
            employee_rec = employee.create(vals)
            applicant.training_ids.write({'employee_id': employee_rec.id})
            applicant.experience_ids.write({'employee_id': employee_rec.id})
            applicant.education_ids.write({'employee_id': employee_rec.id})

            template = self.env.ref('sky_hr_recruitment_custom.pending_applicant_document_email_template')
            email_value = {'email_to': applicant.email_from, 'email_from': self.env.user.email or ''}
            template.send_mail(self.id, email_values=email_value, force_send=True,
                               notif_layout='sky_hr_recruitment_custom.sky_mail_template')
            applicant.state = 'closed'

    def schedule_interview(self):
        """
        This method is used to schedule an interview for the applicant
        This method also sends an email for the scheduled interview
        --------------------------------------------------------------
        @param self: object pointer
        """
        self.ensure_one()
        return {
            'name': _("Schedule Interview"),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'update.schedule.interview.wizard',
            'target': 'new',
        }

    def accept_applicant(self):
        """
        This method is used to accept the applicant and send email
        And move the state of the applicant pending_for_document
        ----------------------------------------------------------
        @param self: object pointer
        """
        self.ensure_one()
        return {
            'name': _("Accept Application"),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'pending.document',
            'target': 'new',
        }

    def reject_applicant(self):
        """
        This method is used to reject the applicant
        -------------------------------------------
        @param self: object pointer
        """
        self.ensure_one()
        return {
            'name': _("Reject Application"),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'reject.applicant.wizard',
            'target': 'new',
        }

    def cancel_applicant(self):
        """
        This method is used to cancel the applicant
        -------------------------------------------
        @param self: object pointer
        """
        self.ensure_one()
        return {
            'name': _("Cancel Application"),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'cancel.applicant.wizard',
            'target': 'new',
        }

    def applicant_detail_print(self):
        """
        This method will print the applicant information along with the uploaded CV
        ---------------------------------------------------------------------------
        @param sefl: object pointer
        """
        self.ensure_one()
        for record in self:
            report_data = self.env['ir.actions.report'].search(
                [('report_name', '=', 'sky_hr_recruitment_custom.report_hr_applicant')])
            report_file_name = gettempdir() + "/" + tools.ustr(report_data.name) + '.pdf'

            data = report_data.render_qweb_pdf([record.id])[0]
            f1 = open(os.path.join(report_file_name), 'wb+')
            f1.write(data)
            f1.close()
            if not record.cv:
                wizard_id = self.env['print.report.wizard'].create({'download_file': base64.encodebytes(data), 'fname': 'Applicant.pdf'}).id
                return {
                    'name': _("Download File"),
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'print.report.wizard',
                    'target': 'new',
                    'res_id': wizard_id
                }

            applicant_cv_file = gettempdir() + "/" + str(self._uid) + "_" + str(record.id)
            f2 = open(os.path.join(applicant_cv_file), 'wb+')
            f2.write(base64.decodebytes(record.cv))
            f2.close()

            # Open the files that have to be merged one by one
            pdf1File = open(report_file_name, 'rb')
            pdf2File = open(applicant_cv_file, 'rb')
            # Read the files that you have opened
            pdf1Reader = PyPDF2.PdfFileReader(pdf1File)
            pdf2Reader = PyPDF2.PdfFileReader(pdf2File)

            # Create a new PdfFileWriter object which represents a blank PDF document
            pdfWriter = PyPDF2.PdfFileWriter()
            # Loop through all the pagenumbers for the first document
            for pageNum in range(pdf1Reader.numPages):
                pageObj = pdf1Reader.getPage(pageNum)
                pdfWriter.addPage(pageObj)
            # Loop through all the pagenumbers for the second document
            for pageNum in range(pdf2Reader.numPages):
                pageObj = pdf2Reader.getPage(pageNum)
                pdfWriter.addPage(pageObj)

            # Now that you have copied all the pages in both the documents, write them into the a new document
            merge_file = gettempdir() + "/" + "merge_%s-%s.pdf" % (self._uid, record.id)
            pdfOutputFile = open(merge_file, 'wb')
            pdfWriter.write(pdfOutputFile)
            # Close all the files - Created as well as opened
            pdfOutputFile.close()
            pdf1File.close()
            pdf2File.close()

            f3 = open(merge_file, 'rb')
            data = f3.read()
            data = base64.encodebytes(data)
            wizard_id = self.env['print.report.wizard'].create({'download_file': data, 'fname': 'Applicant.pdf'}).id
            return {
                'name': _("Download File"),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'print.report.wizard',
                'target': 'new',
                'res_id': wizard_id
            }