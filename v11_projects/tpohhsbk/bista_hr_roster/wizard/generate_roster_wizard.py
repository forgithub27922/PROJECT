import pytz
from datetime import datetime
from dateutil import relativedelta
from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, \
    DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import ValidationError, UserError
import collections


class GenerateRoster(models.TransientModel):
    _name = 'generate.roster'

    type = fields.Selection([('linear', 'Linear'),
                             ('rotational', 'Rotational'),
                             ('weekdays', 'Week Days')], string="Roster Type",
                            default='linear')
    rotation_periods = fields.Integer(string="Rotation Periods")
    shift_id = fields.Many2one('hr.shift.code', string="Shift")
    rotational_shift_ids = fields.Many2many('hr.shift.code', string="Shift")
    weekday_lines = fields.One2many('roster.weekdays.line',
                                    'generate_roster_id',
                                    string="Weekday Lines")
    roster_id = fields.Many2one('hr.roster', string="Roster")

    @api.constrains('rotation_periods', 'weekday_lines')
    def check_rotation_periods(self):
        for data in self:
            if data.type == 'rotational':
                if data.rotation_periods <= 0:
                    raise ValidationError("Rotational period should\
                     be positive.")
                if not data.rotational_shift_ids:
                    raise ValidationError("Please add some shift in line.")
            if data.type == 'weekdays':
                if not data.weekday_lines:
                    raise ValidationError("Please enter weekday in line.")

                """check repeated/missing working day in line"""
                all_day = []
                for line in data.weekday_lines:
                    all_day += [day.name for day in line.week_day]
                active_id = self._context.get('active_id')
                weekoff_ids = self.env['hr.roster'].\
                    browse(active_id).weekoff.ids
                week_days = self.env['weekoff.day'].\
                    search([('id', 'not in', weekoff_ids)])
                working_day_list = [day.name for day in week_days]
                if set(working_day_list) - set(all_day):
                    raise ValidationError("Please add all working\
                    days in line.")

                all_day = [item for item, count in
                           collections.Counter(all_day).items() if count > 1]
                if all_day:
                    raise ValidationError("Day '%s'\
                    repeat in line" % (all_day[0]))

    @api.multi
    def action_generate_roster_line(self):
        """ Generate roster lines based on start date and end date """
        is_hr_holidays_public_installed = self.env['ir.module.module'].sudo().search_count([('state', '=', 'installed'),('name','=', 'hr_public_holidays')])
        if is_hr_holidays_public_installed:
            holiday_obj = self.env['hr.holidays.public']
        active_id = self._context.get('active_id')
        if not active_id:
            raise UserError("Active id not found.")
        roster_id = self.env['hr.roster'].browse(active_id)
        for rec in roster_id:
            rotational_shift_ids = self.rotational_shift_ids.ids
            rotation_periods = self.rotation_periods
            roster_line_vals = []
            start_date = rec.start_date
            end_date = rec.end_date
            temp_date = datetime.strptime(
                start_date, DEFAULT_SERVER_DATE_FORMAT)

            # Calculate Leave
            leave_recs = self.env['hr.holidays'].search(
                ['|', ('date_from', '>=', start_date),
                 ('date_to', '<=', end_date),
                 ('state', '=', 'validate'),
                 ('type', '=', 'remove'),
                 ('employee_id', '=', rec.employee_id.id)])
            # Weekoffs define on Roster
            weekoffs = []
            for weekoff in rec.weekoff:
                weekoffs.append(weekoff.code)

            # Generate lines
            rotate_count = 0
            while temp_date.strftime(DEFAULT_SERVER_DATE_FORMAT) <= end_date:
                holiday_type = ''
                is_public_holiday = False
                if is_hr_holidays_public_installed:
                    is_public_holiday = holiday_obj.is_public_holiday(
                        selected_date=temp_date,
                        employee_id=self.roster_id.employee_id.id)
                if is_public_holiday:
                    holiday_type = 'holiday'
                if temp_date.strftime('%A') in weekoffs:
                    holiday_type = 'weekoff'
                for res in leave_recs:
                    from_dt = datetime.strptime(
                        res.date_from, DEFAULT_SERVER_DATE_FORMAT)
                    from_dt = from_dt.replace(tzinfo=pytz.utc). \
                        astimezone(pytz.timezone(self.env.user.tz or 'UTC'))
                    to_dt = datetime.strptime(
                        res.date_to, DEFAULT_SERVER_DATE_FORMAT)
                    to_dt = to_dt.replace(tzinfo=pytz.utc). \
                        astimezone(pytz.timezone(self.env.user.tz or 'UTC'))
                    if from_dt.strftime(DEFAULT_SERVER_DATE_FORMAT) <= \
                            temp_date.strftime(DEFAULT_SERVER_DATE_FORMAT) <= \
                            to_dt.strftime(DEFAULT_SERVER_DATE_FORMAT):
                        holiday_type = 'leave'
                # delete existing roster line before generating new lines
                if rec.roster_line_ids:
                    self._cr.execute(
                        "delete from hr_roster_line where roster_id=(%s)"
                        % rec.id)
                if self.type == 'linear':
                    roster_line_vals.append(
                        (0,
                         0,
                         {
                             'roster_id': rec.id,
                             'holiday_type': holiday_type,
                             'schedule_date': temp_date. strftime(
                                 DEFAULT_SERVER_DATE_FORMAT),
                             'shift_code_id':
                             not holiday_type and self.shift_id.id or False,
                         }))
                if self.type == 'rotational':
                    if self.rotation_periods < 0:
                        raise ValidationError("Rotational period should\
                         be positive.")
                    if not rotate_count < rotation_periods:
                        rotational_shift_ids = rotational_shift_ids[1:] \
                            + rotational_shift_ids[:1]
                        rotate_count = 0
                    shift_id = rotational_shift_ids[0]
                    roster_line_vals.append(
                        (0,
                         0,
                         {
                             'roster_id': rec.id,
                             'holiday_type': holiday_type,
                             'schedule_date': temp_date. strftime(
                                 DEFAULT_SERVER_DATE_FORMAT),
                             'shift_code_id': not holiday_type and shift_id
                             or False,
                         }))
                    if not holiday_type:
                        rotate_count += 1
                if self.type == 'weekdays':
                    week_dict = {}
                    today_day = temp_date.strftime('%A')
                    for day_line in self.weekday_lines:
                        for day_name in day_line.week_day.mapped('name'):
                            week_dict[day_name] = day_line.shift_id.id

                    roster_line_vals.append(
                        (0,
                         0,
                         {
                             'roster_id': rec.id,
                             'holiday_type': holiday_type,
                             'schedule_date': temp_date. strftime(
                                 DEFAULT_SERVER_DATE_FORMAT),
                             'shift_code_id': not holiday_type and week_dict.
                             get(today_day) or False,
                         }))
                temp_date = temp_date + relativedelta.relativedelta(days=1)
            rec.write({'roster_line_ids': roster_line_vals})
        return True


class RosterWeekdaysLine(models.TransientModel):
    _name = 'roster.weekdays.line'

    generate_roster_id = fields.Many2one('generate.roster', String="Roster")
    week_day = fields.Many2many('weekoff.day', string="Days")
    shift_id = fields.Many2one('hr.shift.code', string="Shift")
