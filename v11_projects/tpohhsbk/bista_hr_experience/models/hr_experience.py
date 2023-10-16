# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from datetime import datetime, timedelta
from dateutil import relativedelta as rdelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as dt, DEFAULT_SERVER_DATE_FORMAT
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrExperience(models.Model):
    _name = 'hr.experience'
    _description = "Employee Experience"
    _rec_name = 'employee_id'

    @api.depends('start_date', 'end_date')
    def _compute_exp(self):
        exp = 0.0
        for rec in self:
            if rec.start_date and rec.end_date:
                st_date = datetime.strptime(rec.start_date, DEFAULT_SERVER_DATE_FORMAT)
                ed_date = datetime.strptime(rec.end_date, DEFAULT_SERVER_DATE_FORMAT)
                rd = rdelta.relativedelta(ed_date, st_date)
                if rd.years or rd.months or rd.days:
                    exp = (rd.years) + (rd.months / 12) + (rd.days / 360)
            rec.experience = exp

    company = fields.Char('Company Name')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    experience = fields.Float('Experience(Years)', compute='_compute_exp')
    relevant = fields.Boolean('Relevant')
    job_id = fields.Many2one('hr.job', 'Designation')
    file_name = fields.Char('File Name')
    experience_letter = fields.Binary('Experience Letter')
    employee_id = fields.Many2one('hr.employee', 'Employee',
                                  ondelete="cascade")

    def _check_date(self):
        for res in self:
            exp_ids = self.search([('start_date', '<=', res.end_date),
                                    ('end_date', '>=', res.start_date),
                                    ('employee_id', '=', res.employee_id.id),
                                    ('id', '<>', res.id)])
            if exp_ids:
                return False
        return True

    _constraints = [
        (_check_date, 'You can not create two experience overlapping \
            with each other !', ['start_date','end_date']),
    ]

    @api.constrains('start_date', 'end_date')
    def check_in_out_dates(self):
        """
        End date date should be greater than the start date.
        """
        if self.end_date and self.start_date:
            if self.end_date < self.start_date:
                raise ValidationError(_('End Date should be greater \
                                         than Start Date in Experience'))
      

class HrEmployee(models.Model):

    _inherit = 'hr.employee'

    @api.depends('experience_ids.relevant', 'experience_ids.experience')
    def _compute_relevant_total_exp(self):
        exp = 0.0
        cur_exp = 0.0
        for rec in self:
            for exp_id in rec.experience_ids:
                cur_exp += exp_id.experience
                if exp_id.relevant:
                    exp += exp_id.experience
            rec.relevant_experience = exp
            rec.total_experience = cur_exp
            rec.total_relevant_experience = rec.relevant_experience + rec.current_experience
            rec.total_past_cur_exp = rec.total_experience + rec.current_experience

    @api.depends('date_employment')
    def _compute_current_exp(self):
        for rec in self:
            experience = 0.0
            if rec.date_employment:
                emp_date = datetime.strptime(rec.date_employment, '%Y-%m-%d').date()
                #rd = rdelta.relativedelta(datetime.now(), emp_date)
                diff_days = (datetime.now().date() - emp_date).days + 1
                experience = diff_days / 365
                # if rd.years or rd.months or rd.days:
                #     experience = (rd.years) + (rd.months / 12) + (rd.days / 365)
            rec.current_experience = experience

    experience_ids = fields.One2many('hr.experience', 'employee_id',
                                     'Experience')
    relevant_experience = fields.Float('Relevant Past Experience',
                                       compute='_compute_relevant_total_exp')
    total_experience = fields.Float('Total Past Experience',
                                    compute='_compute_relevant_total_exp')
    current_experience = fields.Float("Current Company's Experience",
                                      compute='_compute_current_exp')
    total_relevant_experience = fields.Float('Total Relevant Experience',
                                             compute='_compute_relevant_total_exp')
    total_past_cur_exp = fields.Float(String='Total Experience',
                                      compute='_compute_relevant_total_exp')
