# -*- coding: utf-8 -*-

import pytz
from datetime import datetime, timedelta
from dateutil import relativedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import fields, models, api


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    @api.one
    @api.depends('check_in', 'check_out')
    def _compute_hours(self):
        tot_hours = '0:00:00'
        if self.check_out and self.check_in:
            out_time = datetime.strptime(self.check_out,
                                         DEFAULT_SERVER_DATETIME_FORMAT)
            in_time = datetime.strptime(self.check_in,
                                        DEFAULT_SERVER_DATETIME_FORMAT)
            tot_seconds = (out_time - in_time).seconds
            tot_hours = timedelta(seconds=tot_seconds)
        self.total_hours = tot_hours



    total_hours = fields.Char(compute='_compute_hours', string='Hours',
                              help="Total attendance hour.")
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)

    def update_roster_vs_attendance_line(self, res):
        work_hours = act_ot = actual_out = 0.00
        ac_out_date = False
        att_date = res.check_in
        att_date = fields.Date.to_string(fields.Date.from_string(att_date))

        roster_line = self.env['roster.vs.attendance.line'].search([
            ('att_date', '=', att_date),
            ('employee_id', '=', res.employee_id.id),
            ('company_id', '=', res.company_id.id),

        ])
        # fffff
        if res:
            # find actual in and out
            first_check_in = res.check_in or False
            first_check_in = datetime.strptime(
                first_check_in, DEFAULT_SERVER_DATETIME_FORMAT)
            in_date = first_check_in.replace(
                tzinfo=pytz.utc).astimezone(
                pytz.timezone(self.env.user.tz or 'UTC'))
            # Actual Sign in
            in_time = in_date.strftime('%H:%M')
            hour, minutes = in_time.split(':')
            get_in_time = int(hour) * 3600 + int(minutes) * 60
            actual_in = get_in_time / 3600.0
            ac_in_date = datetime.strptime(
                (in_date.strftime('%Y-%m-%d %H:%M:%S')),
                '%Y-%m-%d %H:%M:%S')

            last_check_out = res.check_out or False
            if last_check_out:
                last_check_out = datetime.strptime(
                    last_check_out, '%Y-%m-%d %H:%M:%S')
                out_date = last_check_out.replace(tzinfo=pytz.utc). \
                    astimezone(pytz.timezone(
                    self.env.user.tz or 'UTC'))
                # Actual Sign out
                out_time = out_date.strftime('%H:%M')
                hour, minutes = out_time.split(':')
                get_out_time = int(hour) * 3600 + int(minutes) * 60
                actual_out = get_out_time / 3600.0
                ac_out_date = datetime.strptime(
                    (out_date.strftime('%Y-%m-%d %H:%M:%S')),
                    '%Y-%m-%d %H:%M:%S')
            if ac_out_date and ac_in_date:
                working_time = relativedelta.relativedelta(
                    ac_out_date, ac_in_date)
                work_hours += working_time.hours + (
                    working_time.minutes / 60.0) + (
                                  working_time.seconds / 3600.0)

            shift_duration = roster_line.roster_line_id.shift_code_id.duration
            if work_hours > shift_duration:
                act_ot = work_hours - shift_duration
            if act_ot > 0:
                status = 'Overtime'
            else:
                status = ''
        roster_line.write({
            'actual_sign_in': actual_in,
            'actual_sign_out': actual_out,
            'total_hours': work_hours,
            'working_hours': work_hours,
            'overtime': act_ot,
            'status': status,
        })


    @api.model
    def create(self, vals):
        '''
        TO log employee attendance in roster line realtime bases
        :param vals:
        :return:
        '''
        res = super(HrAttendance, self).create(vals)
        res.update_roster_vs_attendance_line(res)
        return res

    @api.multi
    def write(self, vals):
        '''
        TO log employee attendance in roster line realtime bases
        :param vals:
        :return:
        '''
        res = super(HrAttendance, self).write(vals)
        for rec in self:
            rec.update_roster_vs_attendance_line(rec)
        return res