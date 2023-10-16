# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from bs4 import BeautifulSoup as BSHTML

from odoo import api, fields, models
from odoo.tools.translate import html_translate


class ApplicantHRDocument(models.Model):
    _name = 'applicant.hr.document'
    _rec_name = 'document_id'

    document_id = fields.Many2one('hr.job.document', string="Subject",
                                  required=True)
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)
    employee_id = fields.Many2one('hr.employee', string='Employee')

    def get_report(self):
        """
        Override this method to
        Print hr documents like appointment letter, offer letter etc.
        :return: True
        """
        return True


class HrDocument(models.Model):
    _name = "hr.job.document"
    _inherit = ['mail.thread']

    name = fields.Char(string="Name")
    is_applicant = fields.Boolean('Is applicant')

    applicant_id = fields.Many2one('hr.applicant', string="Applicant")

    document_content = fields.Html(translate=html_translate,
                                   sanitize_attributes=False,
                                   string="Document Content")
    type = fields.Selection([('appo_ltr', 'Appointment Letter'),
                             ('join_ltr', 'Joining Letter'),
                             ('experience', 'Experience'),
                             ('relieve', 'Relieving'),
                             ('reference', 'Reference')],
                            string="Document Type", default='')
    html_translater = fields.Html(string="Remarks", translate=html_translate)
    # fields for EOS
    employee_id = fields.Many2one('hr.employee', string="Employee")
    department_id = fields.Many2one(related="employee_id.department_id",
                                    string="Department")
    date = fields.Date('Date', default=fields.date.today())
    emp_join_date = fields.Date(related="employee_id.date_joining",
                                string="DOJ")
    emp_relieve_date = fields.Date(string="Relieve Date")
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)

    @api.onchange('type')
    def onchange_type(self):
        """
        To change content of letter
        :return:
        """
        if self.type == 'appo_ltr':
            hr_data_appo = self.env.ref(
                'hr_document.hr_document_appointment_letter')
            self.document_content = hr_data_appo.document_content
        elif self.type == 'join_ltr':
            hr_data_join = self.env.ref(
                'hr_document.hr_document_joining_letter')
            self.document_content = hr_data_join.document_content
        elif self.type == 'experience':
            hr_data_ref = self.env.ref(
                'hr_document.hr_document_reference_letter')
            self.document_content = hr_data_ref.document_content
        else:
            self.document_content = ''

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        """
        TO set Relieve date from Exit request
        :return:
        """
        if self.employee_id:
            released_emp = self.env['hr.termination.request'].search(
                [('employee_id', '=', self.employee_id.id),
                 ('state', '=', 'released')], limit=1)
            self.emp_relieve_date = released_emp.relieve_date


    def get_html_field_data(self, field):
        """
        For parse the data from HTML Field.
        ---------------------------------
        :param field:
        :return:
        """
        self.html_translater = ''
        Template = self.env['mail.template']
        if field == 'document_content' and self.document_content:
            if BSHTML(self.document_content, "lxml").text:
                self.html_translater = Template.render_template(
                    self.document_content, 'hr.job.document', self.id)
                return True
            else:
                return False
