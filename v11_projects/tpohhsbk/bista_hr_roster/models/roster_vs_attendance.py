# -*- coding: utf-8 -*-
import pytz
import calendar
from datetime import datetime
from dateutil import relativedelta
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, \
    DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from .hijri import Convert_Date


class RosterVsAttendance(models.Model):
    _name = 'roster.vs.attendance'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one(
        'hr.employee', 'Employee', ondelete="cascade")
    start_date = fields.Date('Start Date')
    start_date_hijri = fields.Char(size=10)
    end_date = fields.Date('End Date')
    end_date_hijri = fields.Char(size=10)
    roster_attendance_line_ids = fields.One2many(
        'roster.vs.attendance.line', 'attendance_id',
        string="Attendance Lines")

    state = fields.Selection([('draft', 'Draft'), ('submit', 'Confirm'),
                              ('cancel', 'Cancel')], default='draft',
                             track_visibility='onchange')
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)

    @api.constrains('start_date', 'end_date')
    def check_date_overlap(self):
        domain = [
            ('start_date', '<=', self.end_date),
            ('end_date', '>=', self.start_date),
            ('id', '!=', self.id),
            ('employee_id', '=', self.employee_id.id)

        ]
        if self.search_count(domain):
            raise ValidationError('You can not overlap \
            roster vs attendance.')

    @api.onchange('start_date', 'end_date')
    def onchange_gregorian_date(self):
        """ Convert Gregorian date to Hijri """
        self.ensure_one()
        if self.start_date:
            self.start_date_hijri = Convert_Date(
                self.start_date, 'english', 'islamic')
        if self.end_date:
            self.end_date_hijri = Convert_Date(
                self.end_date, 'english', 'islamic')

    @api.onchange('start_date_hijri', 'end_date_hijri')
    def onchange_hijri_date(self):
        """ Convert Hijri date to Gregorian """
        self.ensure_one()
        if self.start_date_hijri:
            if self.start_date_hijri[4] != '-' or \
                    self.start_date_hijri[7] != '-':
                raise ValidationError(
                    "Incorrect date format, should be YYYY-MM-DD")
            self.start_date = Convert_Date(
                self.start_date_hijri, 'islamic', 'english')
        if self.end_date_hijri:
            if self.end_date_hijri[4] != '-' or \
                    self.end_date_hijri[7] != '-':
                raise ValidationError(
                    "Incorrect date format, should be YYYY-MM-DD")
            self.end_date = Convert_Date(
                self.end_date_hijri, 'islamic', 'english')

    @api.multi
    def generate_roster_attendance_lines(self):
        """ Generate Roster VS Attendance Entry for given date range"""
        roster_att_line_obj = self.env['roster.vs.attendance.line']
        att_env = self.env['hr.attendance']
        
        
        is_bista_exception_request_installed = self.env['ir.module.module'].sudo().search_count([(
            'state', '=', 'installed'),('name','=', 'bista_exception_request')])
        if is_bista_exception_request_installed:
            exception_request_obj = self.env['request.exception']
            
        is_bista_hr_overtime_installed = self.env['ir.module.module'].sudo().search_count([(
            'state', '=', 'installed'),('name','=', 'bista_hr_overtime')])
        if is_bista_hr_overtime_installed:
            overtime_request_obj = self.env['request.overtime']
            
        for rec in self:
            # Delete Lines
            if rec.roster_attendance_line_ids:
                self._cr.execute(
                    "delete from roster_vs_attendance_line where "
                    "attendance_id=%s" % rec.id)
            start_date = rec.start_date
            end_date = rec.end_date
            temp_date = datetime.strptime(
                start_date, DEFAULT_SERVER_DATE_FORMAT)
            absence = 0
            absence_hours = 0
            calculated_attendance_recs = []
            while temp_date.strftime(DEFAULT_SERVER_DATE_FORMAT) <= end_date:
                shift = False
                pl_in = 0.00
                pl_out = 0.00
                ac_in = 0.00
                ac_out = 0.00
                total_hours = 0.0
                ot = 0.00
                actual_ot = 0.00
                work_hours = 0.00
                exce_hours = 0.00
                status = False
                week = False
                l_leave = False
                l_holiday = False
                attendance_recs = []
                ac_in_date = False
                ac_out_date = False
                taken_break_time = 0
                actual_in = 0
                actual_out = 0
                diff_hour = 0.00
                # Get Planned In/Out
                line = self.env['hr.roster.line'].search([
                    ('schedule_date', '>=', datetime.strftime(
                        temp_date, '%Y-%m-%d %H:%M:%S')),
                    ('schedule_date', '<=', datetime.strftime(
                        temp_date, '%Y-%m-%d 23:59:59')),
                    ('employee_id', '=', rec.employee_id.id),
                    ('roster_id.state', '=', 'confirm')])
                if not line:
                    raise UserError("Roster not found for date %s" % (
                        temp_date.date()))
                for line in line:
                    if line:
                        line.ensure_one()
                        if len(line) > 1:
                            raise Warning(
                                _("You can define roster for same day only one.!"))
                        shift = line.shift_code_id or False
                        pl_in = shift and (
                            not shift.time_in and '0.00' or
                            shift.time_in) or False
                        pl_out = shift and (
                            not shift.time_out and '0.00' or
                            shift.time_out) or False
                        total_planned_hours = pl_out - pl_in
                        # If weekend or weekend and leave true then it will be
                        # consider as weekend
                        if line.holiday_type == 'weekoff':
                            week = True
                        # If leave true but holiday and weekoff false then it will
                        # be consider as leave
                        if line.holiday_type == 'leave':
                            l_leave = True
                        # If holiday or holiday and leave true then it will be
                        # consider as holiday true
                        if line.holiday_type == 'holiday':
                            l_holiday = True

                    attendance_recs = att_env.search(
                        [('check_in', '>=',
                          datetime.strftime(temp_date, '%Y-%m-%d %H:%M:%S')),
                         ('check_in', '<=', datetime.strftime(
                             temp_date, '%Y-%m-%d 23:59:59')),
                         ('check_out', '>=', datetime.strftime(
                             temp_date, '%Y-%m-%d %H:%M:%S')),
                         ('check_out', '<=', datetime.strftime(
                             temp_date, '%Y-%m-%d 23:59:59')),
                         ('employee_id', '=', rec.employee_id.id),
                         ], order='id')
                    # If not checkout
                    if not attendance_recs:
                        attendance_recs = att_env.search(
                            [('check_in', '>=',
                              datetime.strftime(temp_date,
                                                '%Y-%m-%d %H:%M:%S')),
                             ('check_in', '<=', datetime.strftime(
                                 temp_date, '%Y-%m-%d 23:59:59')),
                             ('check_out', '=', False),
                             ('employee_id', '=', rec.employee_id.id),
                             ], order='id')
                    # If not checkin
                    if not attendance_recs:
                        attendance_recs = att_env.search(
                            [('check_out', '>=',
                              datetime.strftime(temp_date,
                                                '%Y-%m-%d %H:%M:%S')),
                             ('check_out', '<=', datetime.strftime(
                                 temp_date, '%Y-%m-%d 23:59:59')),
                             ('check_in', '=', False),
                             ('employee_id', '=', rec.employee_id.id),
                             ], order='id desc')
                    # Count absence and absence hours according to shift
                    if not line.holiday_type == 'leave' and shift and\
                            not attendance_recs:
                        absence += 1
                        absence_hours += shift.duration
                    attendance_recs = [
                        attendance_rec for attendance_rec in attendance_recs if
                        attendance_rec not in calculated_attendance_recs]

                    if attendance_recs:
                        # find actual in and out
                        first_check_in = attendance_recs[0].check_in or False
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

                        last_check_out = attendance_recs[-1:][0].check_out or False
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

                        last_out = False
                        for attend in attendance_recs:
                            check_in = attend.check_in or False
                            check_in = datetime.strptime(
                                check_in, DEFAULT_SERVER_DATETIME_FORMAT)
                            in_date = check_in.\
                                replace(tzinfo=pytz.utc).astimezone(
                                    pytz.timezone(self.env.user.tz or 'UTC'))
                            # Actual Sign in
                            in_time = in_date.strftime('%H:%M')
                            hour, minutes = in_time.split(':')
                            get_in_time = int(hour) * 3600 + int(minutes) * 60
                            ac_in = get_in_time / 3600.0
                            ac_in_date = datetime.strptime(
                                (in_date.strftime('%Y-%m-%d %H:%M:%S')),
                                '%Y-%m-%d %H:%M:%S')
                            check_out = attend.check_out or False
                            if check_out:
                                check_out = datetime.strptime(
                                    check_out, '%Y-%m-%d %H:%M:%S')
                                out_date = check_out.replace(
                                    tzinfo=pytz.utc).astimezone(pytz.timezone(
                                        self.env.user.tz or 'UTC'))
                                # Actual Sign out
                                out_time = out_date.strftime('%H:%M')
                                hour, minutes = out_time.split(':')
                                get_out_time = int(hour) * 3600 + int(minutes) * 60
                                ac_out = get_out_time / 3600.0
                                ac_out_date = datetime.strptime(
                                    (out_date.strftime('%Y-%m-%d %H:%M:%S')),
                                    '%Y-%m-%d %H:%M:%S')
                                if last_out:
                                    taken_break_time += ac_in - last_out
                                    last_out = False
                                last_out = ac_out
                                if ac_out_date and ac_in_date:
                                    working_time = relativedelta.relativedelta(
                                        ac_out_date, ac_in_date)
                                    work_hours += working_time.hours + (
                                        working_time.minutes / 60.0) + (
                                        working_time.seconds / 3600.0)
                    is_exclude_break = line.roster_id.is_exclude_break_time
                    pl_in = line.shift_code_id.time_in
                    pl_out = line.shift_code_id.time_out
                    if not is_exclude_break:
                        total_work_hours = work_hours + taken_break_time
                        shift_duration = line.\
                            shift_code_id.duration + line.\
                            shift_code_id.total_break_duration
                        if total_work_hours > shift_duration:
                            ot = total_work_hours - shift_duration
                    else:
                        shift_duration = line.shift_code_id.duration
                        if work_hours > shift_duration:
                            ot = work_hours - shift_duration

                    # Status
                    temp_date_str = temp_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
                    exception_request_id = False
                    if not ac_in and not pl_in and week:
                        status = 'Weekend'
                    if not ac_in and not pl_in and week and l_leave:
                        status = 'Leave'
                    if not ac_in and l_leave:
                        status = 'Leave'
                    if not ac_in and pl_in and not l_leave and not \
                            l_holiday and not week:
                        status = 'Absence'
                        if temp_date_str > fields.Date.today():
                            status = ''
                    if not ac_in and not pl_in and l_holiday:
                        status = 'Holiday'
                    if not ac_in and not pl_in and l_holiday and l_leave:
                        status = 'Leave'
                    if not ac_in and not pl_in and l_holiday and l_leave and week:
                        status = 'Leave'

                    if is_bista_hr_overtime_installed:
                        overtime_request_id = overtime_request_obj.search(
                            [('request_date', '=', temp_date_str),
                             ('request_duration', '>', 0),
                             ('employee_id', '=', rec.employee_id.id),
                             ('state', '=', 'approve')],
                            limit=1)

                        actual_ot = overtime_request_id.request_duration or 0
                        overtime_request_id = overtime_request_id.id
                        if actual_ot > 0:
                            status = 'Overtime'

                    if is_bista_exception_request_installed:
                        exception_request_id = exception_request_obj.search(
                            [('request_date', '=', temp_date_str),
                             ('action_type', '=', 'add'), ('duration', '>', 0),
                             ('state', '=', 'approve')],
                            limit=1)

                        exce_hours = exception_request_id.duration
                        exception_request_id = exception_request_id.id
                        if exce_hours > 0:
                            status = 'Exception'
                    total_hours = work_hours + exce_hours
                    overtime_request_id = False
                    diff_hour = total_planned_hours - total_hours
                    # Create Attendance Vs Roster Line
                    vals = {
                        'attendance_id': rec.id,
                        'roster_line_id': line.id,
                        'att_date': temp_date_str,
                        'planned_sign_in': pl_in,
                        'planned_sign_out': pl_out,
                        'actual_sign_in': actual_in,
                        'actual_sign_out': actual_out,
                        'overtime': ot,
                        'tota_break_time': line.shift_code_id.total_break_duration,
                        'taken_break_time': taken_break_time,
                        'diff_hours': diff_hour,
                        'working_hours': work_hours,
                        'total_hours': total_hours,
                        'status': status,
                    }
                    if is_bista_hr_overtime_installed:
                        vals.update({'overtime_request_id': overtime_request_id,
                                     'actual_overtime': actual_ot})
                    if is_bista_exception_request_installed:
                        vals.update({
                            'exception_hours': exce_hours,
                            'exception_request_id': exception_request_id or False,
                            })
                    roster_att_line_obj.create(vals)
                    temp_date = temp_date + relativedelta.relativedelta(days=1)
        return True

    @api.multi
    def action_cancel(self):
        self.state = 'cancel'

    @api.multi
    def action_submit(self):
        self.state = 'submit'

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state == 'submit':
                raise UserError(_('You cannot delete confirmed recored.'))
        return super(RosterVsAttendance, self).unlink()

    @api.model
    def update_roster_vs_attendance(self):
        """this method called by Cron Job to update roster hours"""
        today_date = fields.Date.from_string(fields.Date.today())
        first_day = today_date - relativedelta.relativedelta(
            days=fields.Date.from_string(fields.Date.today()).day - 1)

        last_day_month = calendar.monthrange(today_date.year,
                                             today_date.month)[1]
        diff_days = last_day_month - \
                    fields.Date.from_string(fields.Date.today()).day
        last_Date = today_date + relativedelta.relativedelta(
            days=diff_days)

        att_ids = self.env['roster.vs.attendance'].search(
            [('state', '=', 'draft'),
             ('start_date', '>=', first_day),
             ('end_date', '<=', last_Date)])

        for rec in att_ids:
            rec.generate_roster_attendance_lines()


class RosterVsAttendanceLine(models.Model):
    _name = 'roster.vs.attendance.line'

    @api.multi
    @api.depends('att_date')
    def _get_weekday(self):
        for att_line in self:
            if att_line.att_date:
                att_line.week_day = datetime.strptime(
                    att_line.att_date,
                    DEFAULT_SERVER_DATE_FORMAT).strftime('%A')

    attendance_id = fields.Many2one('roster.vs.attendance',
                                    string="Attendance", ondelete="cascade")
    roster_line_id = fields.Many2one(
        'hr.roster.line',
        string="Roster Line",
        ondelete="restrict")
    att_date = fields.Date('Date')
    week_day = fields.Char(compute="_get_weekday", string='Week Day')
    planned_sign_in = fields.Float('Planned Sign In')
    planned_sign_out = fields.Float('Planned Sign Out')
    actual_sign_in = fields.Float('Actual Sign In')
    actual_sign_out = fields.Float('Actual Sign Out')
    tota_break_time = fields.Float(string="Planned Break")
    taken_break_time = fields.Float(string="Actual Break")
    diff_hours = fields.Float(string="Difference Hours")
    working_hours = fields.Float('Actual Working Hours')
    total_hours = fields.Float('Total Hours')
    status = fields.Char(string="Status", copy=False)
    employee_id = fields.Many2one(
        related='attendance_id.employee_id',
        relation='hr.employee',
        string='Employee',
        store=True,
        ondelete="restrict")
    comment = fields.Text("Comment")
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)

