from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
from datetime import date
from datetime import datetime
import calendar
import pytz

week_list = [('0', 'Monday'),
             ('1', 'Tuesday'),
             ('2', 'Wednesday'),
             ('3', 'Thursday'),
             ('4', 'Friday'),
             ('5', 'Saturday'),
             ('6', 'Sunday')]
month_dict = {'1': 'January',
              '2': 'February',
              '3': 'March',
              '4': 'April',
              '5': 'May',
              '6': 'June',
              '7': 'July',
              '8': 'August',
              '9': 'September',
              '10': 'October',
              '11': 'November',
              '12': 'December'}


class TimeTrackingLine(models.Model):
    _inherit = 'time.tracking.line'

    pub_holiday = fields.Boolean('Public Holiday')
    leave = fields.Boolean('Leave')
    vacation = fields.Boolean('Vacation')


class TimeTracking(models.Model):
    _inherit = 'time.tracking'

    def generate_tracking(self):
        """
        This is a method which generates the complete time tracking for the Employees
        """
        tt_line_obj = self.env['time.tracking.line']
        pub_hol_line_obj = self.env['hr.public.holidays.line']
        leave_obj = self.env['hr.leave']
        addition_obj = self.env['hr.addition']
        penalty_obj = self.env['hr.penalty']
        cr_dt = fields.Date.today()

        month_cal = calendar.monthrange(cr_dt.year, cr_dt.month)
        first_day = date(cr_dt.year, cr_dt.month, 1)
        last_day = date(cr_dt.year, cr_dt.month, month_cal[1])

        time_tracking_records = self.search([('start_date', '=', first_day), ('end_date', '=', last_day)])
        for rec in time_tracking_records:
            current_date = date(cr_dt.year, cr_dt.month, 1)
            if rec.employee_id.starting_date:
                if rec.employee_id.starting_date >= current_date and rec.employee_id.starting_date <= cr_dt:
                    current_date = rec.employee_id.starting_date

            rec.schedule_id = rec.set_schedule(rec.employee_id, rec.schedule_id)
            schedule_lines = rec.schedule_id.attendance_ids
            schedule_dict = {}
            # Get the Start Date and End Date for each day from the work schedule
            for day in week_list:
                day_lines = schedule_lines.filtered(lambda r: r.dayofweek == day[0])
                if day_lines:
                    break_hours = sum([dl.break_hours for dl in day_lines])
                    work_hours = sum([dl.working_hours for dl in day_lines])
                    start_time = min([dl.hour_from for dl in day_lines])
                    end_time = max([dl.hour_to for dl in day_lines])
                    schedule_dict.update({day[0]: {'start_time': start_time,
                                                   'end_time': end_time,
                                                   'break_hours': break_hours,
                                                   'working_hours': work_hours}})
            # Get the Week offs
            week_off_lines = rec.schedule_id.week_off_ids
            week_off_dict = {}
            for day in week_list:
                wo_line = week_off_lines.filtered(lambda r: r.week_day == day[0])
                if wo_line:
                    week_off_dict[wo_line.week_day] = []
                    if wo_line.week_1:
                        week_off_dict[wo_line.week_day].append(1)
                    if wo_line.week_2:
                        week_off_dict[wo_line.week_day].append(2)
                    if wo_line.week_3:
                        week_off_dict[wo_line.week_day].append(3)
                    if wo_line.week_4:
                        week_off_dict[wo_line.week_day].append(4)
                    if wo_line.week_5:
                        week_off_dict[wo_line.week_day].append(5)
            # Fetch Public Holidays
            first_year_day = date(rec.year, 1, 1)
            last_year_day = date(rec.year, 12, 31)
            pub_holidays = pub_hol_line_obj.search([('date', '>=', first_year_day),
                                                    ('date', '<=', last_year_day)])
            # Generate Lines of Employee Tracking for the Month and Year
            while current_date <= cr_dt:
                flag = rec.tracking_line_ids.filtered(lambda r: r.date == current_date)
                if flag:
                    # Go to Next Date
                    current_date += relativedelta(days=1)
                    continue
                wo = False
                vals = {
                    'name': 'Absent',
                    'date': current_date,
                    'day': str(current_date.weekday()),
                    'tracking_id': rec.id,
                    'pub_holiday': False,
                    'week_off': False,
                    'leave': False,
                    'vacation': False
                }
                # Check whether it's a public holiday or not
                pubs = pub_holidays.filtered(lambda r: r.date == current_date)
                if pubs.ids:
                    for pub in pubs:
                        vals.update({
                            'name': pub.name,
                            'pub_holiday': True
                        })
                else:
                    # Check whether it's a Week off or not
                    if str(current_date.weekday()) in week_off_dict.keys():
                        week_number = (current_date.day - 1) // 7 + 1
                        if week_number in week_off_dict[str(current_date.weekday())]:
                            wo = True
                    if wo:
                        # If Week Off mention Week Off
                        vals.update({
                            'name': 'Week - Off',
                            'week_off': True
                        })
                    else:
                        # Check for Leaves
                        leaves = leave_obj.search([('employee_id', '=', rec.employee_id.id),
                                                   ('leave_type', '=', 'leave'),
                                                   ('state', 'in', ('validate', 'validate1')),
                                                   ('request_date_from', '=', current_date)])
                        if leaves.ids:
                            for leave in leaves:
                                if leave.start_time:
                                    vals.update({
                                    'name': 'Leave',
                                    'leave': True,
                                    'approved_leave_start_time': leave.start_time,
                                    'approved_leave_end_time': leave.end_time,
                                })
                        # Check for Vacations
                        vacations = leave_obj.search([('employee_id', '=', rec.employee_id.id),
                                                      ('leave_type', '=', 'vacation'),
                                                      ('state', 'in', ('validate', 'validate1')),
                                                      ('request_date_from', '<=', current_date),
                                                      ('request_date_to', '>=', current_date)])
                        if vacations.ids:
                            vals.update({
                                'name': 'Vacation',
                                'vacation': True,
                            })
                        if str(current_date.weekday()) not in schedule_dict.keys():
                            raise ValidationError(_(
                                'Kindly configure weekoffs for the %s Working Schedule!' % rec.schedule_id.name))
                        # If working day add start and end time, break hours and working hours
                        vals.update({
                            'planned_start_time': schedule_dict.get(str(current_date.weekday()), {}).get('start_time', 0.0),
                            'planned_end_time': schedule_dict.get(str(current_date.weekday()), {}).get('end_time', 0.0),
                            'planned_break_hours': schedule_dict.get(str(current_date.weekday()), {}).get('break_hours', 0.0),
                            'planned_hours': schedule_dict.get(str(current_date.weekday()), {}).get('working_hours', 0.0)
                        })

                # Create Tracking Line
                tracking_rec = tt_line_obj.create(vals)

                additions = addition_obj.search([('date', '=', current_date), ('employee_id', '=', rec.employee_id.id)])
                for add in additions:
                    add.tracking_line_id = tracking_rec.id

                penalties = penalty_obj.search([('date', '=', current_date), ('employee_id', '=', rec.employee_id.id)])
                for pen in penalties:
                    pen.tracking_line_id = tracking_rec.id

                # Go to Next Date
                current_date += relativedelta(days=1)

            rec.state = 'open'

    def compute_tracking(self):
        """
        This method will be used to update the tracking of each day for all employees
        -----------------------------------------------------------------------------
        @param self: object pointer
        """
        att_obj = self.env['hr.attendance']
        exc_obj = self.env['hr.time.exception']
        pub_obj = self.env['hr.public.holidays.line']
        leave_obj = self.env['hr.leave']
        for rec in self:
            week_off_lines = rec.schedule_id.week_off_ids
            week_off_dict = {}
            for day in week_list:
                wo_line = week_off_lines.filtered(lambda r: r.week_day == day[0])
                if wo_line:
                    week_off_dict[wo_line.week_day] = []
                    if wo_line.week_1:
                        week_off_dict[wo_line.week_day].append(1)
                    if wo_line.week_2:
                        week_off_dict[wo_line.week_day].append(2)
                    if wo_line.week_3:
                        week_off_dict[wo_line.week_day].append(3)
                    if wo_line.week_4:
                        week_off_dict[wo_line.week_day].append(4)
                    if wo_line.week_5:
                        week_off_dict[wo_line.week_day].append(5)
            pubs = pub_obj.search([('date', '>=', rec.start_date), ('date', '<=', rec.end_date)])
            # calculate on a daily basis the attendance of the employee and fill up in actual start and end time.
            for line in rec.tracking_line_ids:
                # Get the start and end time of the day
                st_dt = datetime(line.date.year, line.date.month, line.date.day, 0, 0, 0)
                en_dt = datetime(line.date.year, line.date.month, line.date.day, 23, 59, 59)
                # Search for day's attendances and set it in the Tracking
                attendances = att_obj.search([('employee_id', '=', rec.employee_id.id),
                                              ('check_in', '>=', st_dt),
                                              ('check_in', '<=', en_dt)])
                attendances.write({'tracking_line_id': line.id})
                # Set the start time and end time from the attendances
                first_sign_in = False
                last_sign_out = False
                for attendance in attendances:
                    c_in = attendance.check_in.replace(tzinfo=pytz.utc).astimezone( \
                        pytz.timezone(self.env.user.tz or 'UTC'))
                    c_in_time = c_in.hour + c_in.minute / 60.0
                    if not first_sign_in or (first_sign_in > c_in_time):
                        first_sign_in = c_in_time
                    if attendance.check_out:
                        c_out = attendance.check_out.replace(tzinfo=pytz.utc).astimezone( \
                            pytz.timezone(self.env.user.tz or 'UTC'))
                        c_out_time = c_out.hour + c_out.minute / 60.0
                        if not last_sign_out or (last_sign_out < c_out_time):
                            last_sign_out = c_out_time
                    line.actual_start_time = first_sign_in
                    line.actual_end_time = last_sign_out
                # Fetch the exceptions to be added on tracking lines
                excs = exc_obj.search([('date', '=', line.date),
                                       ('employee_id', '=', rec.employee_id.id)])
                for exc in excs:
                    # Add the reference of exceptions to date
                    exc.write({'tracking_line_id': line.id})
                line_vals = {
                    'pub_holiday': False,
                    'vacation': False,
                    'week_off': False,
                    'leave': False,
                    'name': 'Absent'
                }
                cr_pubs = pubs.filtered(lambda r: r.date == line.date)
                if cr_pubs.ids:
                    line_vals = {
                        'name': ','.join(cr_pubs.mapped('name')),
                        'pub_holiday': True
                    }
                else:
                    # WEEK OFF
                    wo = False
                    if str(line.date.weekday()) in week_off_dict.keys():
                        week_number = (line.date.day - 1) // 7 + 1
                        if week_number in week_off_dict[str(line.date.weekday())]:
                            wo = True
                    if wo:
                        # If Week Off mention Week Off
                        line_vals = {
                            'name': 'Week - Off',
                            'week_off': True,
                        }
                    else:
                        leaves = leave_obj.search([('employee_id', '=', rec.employee_id.id),
                                                   ('leave_type', '=', 'leave'),
                                                   ('state', 'in', ('validate', 'validate1')),
                                                   ('request_date_from', '=', line.date)])


                        if leaves.ids:
                            for leave in leaves:
                                if leave.start_time:
                                    line_vals.update({
                                        'name': 'Leave',
                                        'leave': True,
                                        'approved_leave_start_time': leave.start_time,
                                        'approved_leave_end_time': leave.end_time,
                                    })
                        else:
                            # Check for Vacations
                            vacations = leave_obj.search([('employee_id', '=', rec.employee_id.id),
                                                          ('leave_type', '=', 'vacation'),
                                                          ('state', 'in', ('validate', 'validate1')),
                                                          ('request_date_from', '<=', line.date),
                                                          ('request_date_to', '>=', line.date)])
                            if vacations.ids:
                                line_vals.update({
                                    'name': 'Vacation',
                                    'vacation': True,
                                })
                            else:
                                if line.actual_start_time:
                                    line_vals.update({
                                        'name': 'Working Day',
                                    })
                line.write(line_vals)

    def set_schedule(self, employee, work_schedule):
        """
        This method will be used for setting working schedule on time tracking according to the date
        --------------------------------------------------------------------------------------------
        @param self: object pointer
        @param employee: recordset of employee
        @param work_schedule: recordset of working schedule
        """
        schedule_time_line = self.env['schedule.time'].search([('employee_id', '=', employee.id),
                                                               ('from_date', '<=', datetime.now().day),
                                                               ('to_date', '>=', datetime.now().day)], limit=1)

        if not schedule_time_line.id:
            schedule_time_line = self.env['schedule.time'].search([('employee_id', '=', employee.id),
                                                                   ('from_date', '=', 0), ('to_date', '=', 0)], limit=1)

        if schedule_time_line.id:
            return schedule_time_line.working_schedule_id.id

        else:
            return work_schedule.id
