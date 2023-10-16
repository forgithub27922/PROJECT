from odoo import models, fields, api
from datetime import datetime
import pytz


class ApplicantInterview(models.Model):
    _name = 'hr.interview'
    _description = 'Interview'

    _rec_name = 'applicant_id'

    interview_date = fields.Date('Interview Date')
    interview_time = fields.Float('Interview Time')
    interview_date_time = fields.Datetime('Interview Date Time', compute='_calc_datetime', store=True)
    interview_location = fields.Char('Interview Location')
    applicant_id = fields.Many2one('hr.applicant', 'Applicant')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)
    state = fields.Selection([('draft', 'Scheduled'),
                              ('in_progress', 'In Progress'),
                              ('done', 'Completed')], 'State', default='draft')

    @api.depends('interview_date', 'interview_time')
    def _calc_datetime(self):
        """
        This method will calcualte the datetime for the interview.
        ----------------------------------------------------------
        @param self: object pointer
        """
        for interview in self:
            int_time = self.interview_time
            int_date = self.interview_date
            int_hour = int(int_time)
            fl_int_min = (int_time - int_hour) * 100
            int_min = round(fl_int_min * 60.0 / 100.0)
            int_datetime = datetime(int_date.year, int_date.month, int_date.day, int_hour, int_min)
            timezone = pytz.timezone(self.env.user.tz)
            act_datetime_local = timezone.localize(int_datetime, is_dst=False)
            act_datetime = act_datetime_local.astimezone(pytz.utc).replace(tzinfo=None)
            interview.interview_date_time = act_datetime

    def start_interview(self):
        """
        This method will put the interview in progress
        ----------------------------------------------
        @param self: object pointer
        """
        for interview in self:
            interview.state = 'in_progress'

    def complete_interview(self):
        """
        This method will put the interview in complete state
        ----------------------------------------------------
        @param self: object pointer
        """
        for interview in self:
            interview.state = 'done'

    def reset_interview(self):
        """
        This method will put the interview in draft state
        -------------------------------------------------
        @param self: object pointer
        """
        for interview in self:
            interview.state = 'draft'
