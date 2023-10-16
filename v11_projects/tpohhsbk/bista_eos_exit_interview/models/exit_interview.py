# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models
from odoo.addons.bista_hijri_date.models.hijri import Convert_Date
from odoo.exceptions import ValidationError


class ExitInterview(models.Model):
    _name = 'exit.interview'
    _description = "Exit Interview"

    name = fields.Char('Name')
    employee_id = fields.Many2one(
        'hr.employee', 'Employee', ondelete="cascade")
    emp_id = fields.Char(related="employee_id.emp_id", string='Employee ID')
    department_id = fields.Many2one(related="employee_id.department_id")
    manager_id = fields.Many2one(related="employee_id.parent_id",
                                 string='Manager')
    job_id = fields.Many2one(related="employee_id.job_id", string="Job Title")
    date = fields.Date('Exit Date')
    date_hijri = fields.Char(size=10)
    reason = fields.Text('Reason')
    survey_ans = fields.Many2one('survey.user_input', string='Survey Answers')
    exit_interview_form_id = fields.Many2one('survey.survey',
                                             string='Exit Interview Form')
    state = fields.Selection([('draft', 'Draft'),
                              ('submit', 'Submit')],
                             default='draft')
    company_id = fields.Many2one('res.company', string="Company",
                                 default=lambda self: self.env.user.company_id)


    @api.multi
    def state_submit(self):
        """
        Set request state to submit
        :return: None
        """
        for rec in self:
        # if rec.exit_interview_form_id:
            survey_exists = self.env['survey.user_input'].search([
                ('survey_id', '=', rec.exit_interview_form_id.id),
                ('user_id', '=', self._uid)
            ])
            rec.state = 'submit'
            rec.survey_ans = survey_exists and survey_exists.id

    @api.multi
    def fill_exit_interview(self):
        """
        To allow exit request initiator only once to fill survey.
        :return: res
        """
        res = {}
        for rec in self:
            if rec.exit_interview_form_id:
                survey_exists = self.env['survey.user_input'].search([
                    ('survey_id', '=', rec.exit_interview_form_id.id),
                    ('user_id', '=', self._uid)
                ])
                if survey_exists:
                    raise ValidationError("You can not fill again.")
                res = rec.exit_interview_form_id.action_test_survey()

        return res

    @api.onchange('date')
    def onchange_gregorian_date(self):
        """
        Convert Gregorian date to Hijri
        :return: None
        """
        self.ensure_one()
        if self.date:
            self.date_hijri = Convert_Date(
                self.date, 'english', 'islamic')

    @api.onchange('date_hijri')
    def onchange_hijri_date(self):
        """
        Convert Hijri date to Gregorian
        :return: None
        """
        self.ensure_one()
        if self.date_hijri:
            if self.date_hijri[4] != '-' or self.date_hijri[7] != '-':
                raise ValidationError(
                    "Incorrect date format, should be YYYY-MM-DD")
            self.date = Convert_Date(
                self.date_hijri, 'islamic', 'english')
