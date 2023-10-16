# -*- coding: utf-8 -*-

from datetime import datetime
from dateutil import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError



class HrHolidays(models.Model):
    _inherit = 'hr.holidays'

    @api.model
    def action_set_leave_type(self, employee, holiday_date):
        roster_line_obj = self.env['hr.roster.line']
        roster_vs_attnd_obj = self.env['roster.vs.attendance']
        roster_line = roster_line_obj.search([
            ('schedule_date', '=', holiday_date),
            ('roster_id.employee_id', '=', employee),
            ('roster_id.state', '!=', 'cancel')])
        roster_line.write({'holiday_type': 'leave'})
        roster_vs_attnd_rec = roster_vs_attnd_obj.search([
            ('employee_id', '=', employee),
            ('state', '=', 'draft'),
            ('start_date', '<=', holiday_date),
            ('end_date', '>=', holiday_date)])
        if roster_vs_attnd_rec:
            roster_vs_attnd_rec.generate_roster_attendance_lines()
        return True


    @api.multi
    def action_approve(self):
        result = super(HrHolidays, self).action_approve()
        for rec in self:
            if rec.type == 'remove' and rec.holiday_status_id and \
                not rec.holiday_status_id.double_validation:
                start_date = rec.date_from
                end_date = rec.date_to
                tmp_date = datetime.today()
                while tmp_date.strftime(DEFAULT_SERVER_DATE_FORMAT) <= datetime.today().strftime(DEFAULT_SERVER_DATE_FORMAT):
                    
                    employee = rec.employee_id.id
                    rec.action_set_leave_type(employee, tmp_date.strftime(
                        DEFAULT_SERVER_DATE_FORMAT))
                    tmp_date = tmp_date + relativedelta.relativedelta(days=1)
        return result

    @api.multi
    def action_validate(self):
        result = super(HrHolidays, self).action_validate()
        for rec in self:
            if rec.type == 'remove' and rec.date_from:
                start_date = rec.date_from
                end_date = rec.date_to
                tmp_date = datetime.strptime(
                    start_date, DEFAULT_SERVER_DATE_FORMAT)
                while tmp_date.strftime(
                    DEFAULT_SERVER_DATE_FORMAT) <= rec.date_to:
                    employee = rec.employee_id.id
                    rec.action_set_leave_type(employee, tmp_date.strftime(
                        DEFAULT_SERVER_DATE_FORMAT))
                    tmp_date = tmp_date + relativedelta.relativedelta(days=1)
        return result