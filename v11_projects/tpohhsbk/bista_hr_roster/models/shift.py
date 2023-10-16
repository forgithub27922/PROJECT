# -*- coding: utf-8 -*-

from datetime import datetime
from dateutil import relativedelta
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class HrShiftCode(models.Model):
    _name = 'hr.shift.code'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'code'

    def calculate_durations(self, time_in, time_out):
        """
        Return time duration between two float value
        param : time_in, time_out
        return: duration between two time
        """

        if time_out or time_in:
            time_in = '{0:02.0f}:{1:02.0f}'.format(
                *divmod(time_in * 60, 60))
            time_out = '{0:02.0f}:{1:02.0f}'.format(
                *divmod(time_out * 60, 60))
            test_time_in = time_in.split(":")
            test_time_out = time_out.split(":")
            if int(test_time_in[0]) < 0.0 or int(test_time_in[0]) > 23 or \
                    int(test_time_in[1]) > 59 or int(test_time_out[0]) < 0.0 \
                    or int(test_time_out[0]) > 23 or \
                    int(test_time_out[1]) > 59:
                raise ValidationError("Time must be \
                in between 00:00 to 23:59.")
            time_in_str = datetime.strptime(time_in, '%H:%M')
            time_out_str = datetime.strptime(time_out, '%H:%M')
            if not time_out:
                time_out_str = datetime.strptime(
                    time_out, '%H:%M') + relativedelta.relativedelta(
                    days=1)
            elif not time_in:
                time_out_str = datetime.strptime(
                    time_out, '%H:%M') + relativedelta.relativedelta(
                    days=-1)
            time_diff = time_out_str - time_in_str
            minutes = int(time_diff.total_seconds() / 60)
            time_in_float = time_in or 24.0
            time_out_float = time_out or 24.0
            if time_out_float > time_in_float:
                duration = minutes / 60.0
                return duration
            if time_out_float < time_in_float:
                duration = (minutes / 60.0) + 24
                return duration

    @api.depends('time_in', 'time_out', 'break_time_ids.break_in_time',
                 'break_time_ids.break_out_time')
    def _get_duration(self):
        """ Calculate working time in shift code based on Time In/Out
        and Break In/Out """
        for shift in self:
            shift.is_night_shift = False
            if shift.time_out or shift.time_in:
                duration = shift.calculate_durations(shift.time_in,
                                                     shift.time_out)
                break_duration = sum(shift.break_time_ids.mapped('duration'))
                shift.total_break_duration = break_duration
                shift_actual_duration = duration - break_duration
                shift.duration = shift_actual_duration

    @api.multi
    @api.constrains('time_in', 'time_out')
    def _check_time(self):
        for line in self.break_time_ids:
            if self.time_in > line.break_in_time or self.\
                    time_out < line.break_out_time:
                raise ValidationError("Break time must be in between\
                shift IN and OUT time.")

    code = fields.Char(string='Code', required=True,
                       track_visibility='onchange')
    description = fields.Char(string='Description')
    time_in = fields.Float(string='Time In', track_visibility='onchange')
    time_out = fields.Float(string='Time Out', track_visibility='onchange')
    total_break_duration = fields.Float(compute=_get_duration,
                                        string="Total Break Time")
    duration = fields.Float(compute=_get_duration, string="Duration")
    break_time_ids = fields.One2many('break.time.line', 'shift_id',
                                     string="Break Time")
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)

    _sql_constraints = [('shift_code_uniq', 'unique (code)',
                         "The Code must be unique, "
                         "This code is already assigned.")]


class BreakTimeLine(models.Model):
    _name = 'break.time.line'

    @api.depends('break_in_time', 'break_out_time')
    def _get_duration(self):
        """ Calculate  break duration"""
        shift_id = self.env['hr.shift.code']
        for line in self:
            if line.break_out_time or line.break_in_time:
                duration = shift_id.calculate_durations(line.break_in_time,
                                                        line.break_out_time)
                line.duration = duration

    shift_id = fields.Many2one('hr.shift.code', string="Shift Code")
    name = fields.Char(string="Name", size=20)
    break_in_time = fields.Float(string="In Time", required=True)
    break_out_time = fields.Float(string="Out Time", required=True)
    duration = fields.Float(string="Break Duration", compute=_get_duration,
                            store=True)
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)

    @api.onchange('break_in_time', 'break_out_time')
    def onchange_break_time(self):
        if self.break_in_time > 0.0 and self.break_out_time > 0.0:
            if self.break_in_time < self.shift_id.time_in or \
                    self.break_in_time \
                    > self.shift_id.time_out or self.break_out_time \
                    < self.shift_id.time_in or self.break_out_time \
                    > self.shift_id.time_out:
                raise ValidationError("Break time must be in between Shift\
                 Time In and Time Out.")

    @api.multi
    @api.constrains('break_in_time', 'break_out_time')
    def _check_time(self):
        self.ensure_one()
        if self.break_in_time >= self.break_out_time:
            raise ValidationError(
                "Break Out time must be greater then In Time.")

        domain = [
            ('break_in_time', '<=', self.break_out_time),
            ('break_out_time', '>=', self.break_in_time),
            ('id', '!=', self.id),
            ('shift_id', '=', self.shift_id.id)
        ]
        if self.search_count(domain):
            raise ValidationError('You can not have 2 break that\
            overlaps on same time!')
