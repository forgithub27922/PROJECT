# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Education(models.Model):
    _name = 'hr.education'
    _description = 'Education'

    name = fields.Char('Name')
    institute = fields.Char('Institute')
    applicant_id = fields.Many2one('hr.applicant', 'Applicant')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('Graduation Date')
    final_grade = fields.Selection([('excellent', 'Excellent'),
                                   ('very good', 'Very Good'),
                                    ('good', 'Good'),
                                    ('sufficient', 'Sufficient')
                                    ], 'Final Grade')
    employee_id = fields.Many2one('hr.employee', 'Employee')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)


class Training(models.Model):
    _name = 'hr.training'
    _description = 'Training'

    name = fields.Char('Training')
    institute_name = fields.Char('Institute')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    applicant_id = fields.Many2one('hr.applicant', 'Applicant')
    employee_id = fields.Many2one('hr.employee', 'Employee')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)

    @api.constrains('start_date', 'end_date')
    def check_dates(self):
        """
        This will check whether the start date is earlier than the end date or not
        ---------------------------------------------------------------------------
        @param self: object pointer
        """
        for training in self:
            if (training.start_date and training.end_date) and not (training.start_date < training.end_date):
                raise ValidationError(_('The Start Date must be prior to End Date!'))


class Experience(models.Model):
    _name = 'hr.experience'
    _description = 'Experience'

    name = fields.Char('Employer Name')
    job_id = fields.Many2one('hr.job', 'Position')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    applicant_id = fields.Many2one('hr.applicant', 'Applicant')
    employee_id = fields.Many2one('hr.employee', 'Employee')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)

    @api.constrains('start_date', 'end_date')
    def check_dates(self):
        """
        This will check whether the start date is earlier than the end date or not
        ---------------------------------------------------------------------------
        @param self: object pointer
        """
        for exp in self:
            if (exp.start_date and exp.end_date) and not (exp.start_date < exp.end_date):
                raise ValidationError(_('The Start Date must be prior to End Date!'))

