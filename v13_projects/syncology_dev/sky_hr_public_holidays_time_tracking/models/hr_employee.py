from odoo import models, fields, api, _
import calendar
from datetime import date


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


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.model_create_multi
    def create(self, vals_lst):
        """
        Overridden create method to create time tracking of employee
        ------------------------------------------------------------
        @param self: object pointer
        @param vals_lst: A dictionary containing fields and values
        """
        # pub_hol_line_obj = self.env['hr.public.holidays.line']
        res = super(HrEmployee, self).create(vals_lst)
        res_name = res and res.name or '/'
        tracking_obj = self.env['time.tracking']
        cr_dt = fields.Date.today()
        month_cal = calendar.monthrange(cr_dt.year, int(cr_dt.month))

        schedule_dict = {}
        # Get the Start Date and End Date for each day from the work schedule
        for day in week_list:
            schedule_lines = res.resource_calendar_id.attendance_ids
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

        tracking_line_vals = {
            'name': 'Absent',
            'date': cr_dt,
            'day': str(cr_dt.weekday()),
            'pub_holiday': False,
            'week_off': False,
            'leave': False,
            'vacation': False,
            'planned_start_time': schedule_dict.get(str(cr_dt.weekday()), {}).get('start_time', 0.0),
            'planned_end_time': schedule_dict.get(str(cr_dt.weekday()), {}).get('end_time', 0.0),
            'planned_break_hours': schedule_dict.get(str(cr_dt.weekday()), {}).get('break_hours', 0.0),
            'planned_hours': schedule_dict.get(str(cr_dt.weekday()), {}).get('working_hours', 0.0)
        }

        tracking_ids = tracking_obj.search([('employee_id', '=', res.id),
                                            ('month', '=', str(cr_dt.month))])

        if tracking_ids:
            tracking_ids.tracking_line_ids = [(0, 0, tracking_line_vals)]

        else:
            if res.ids:
                tracking_vals = {
                    'name': month_dict[str(cr_dt.month)] + '-' + str(cr_dt.year) + ' : ' + res_name,
                    'month': str(cr_dt.month),
                    'year': cr_dt.year,
                    'employee_id': res.id,
                    'schedule_id': res.resource_calendar_id.id,
                    'start_date': date(cr_dt.year, int(cr_dt.month), 1),
                    'end_date': date(cr_dt.year, int(cr_dt.month), month_cal[1]),
                    'tracking_line_ids':  [
                            (0, 0, tracking_line_vals)]
                }
                tracking_obj.create(tracking_vals)
        return res

    def write(self, vals):
        """
        Overridden write method to
        -----------------------------------------------------
        @param self: object pointer
        @param vals: a dictionary containing fields and values
        :return: True
        """
        res = super(HrEmployee, self).write(vals)
        time_tracking_obj = self.env['time.tracking']
        for emp in self:
            if vals.get('resource_calendar_id', False):
                cr_dt = fields.Date.today()
                month_cal = calendar.monthrange(cr_dt.year, cr_dt.month)
                first_day = date(cr_dt.year, cr_dt.month, 1)
                last_day = date(cr_dt.year, cr_dt.month, month_cal[1])

                time_tracking = time_tracking_obj.search([('employee_id', '=', emp.id), ('start_date', '=', first_day),
                                                          ('end_date', '=', last_day)])
                time_tracking.write({'schedule_id': vals.get('resource_calendar_id')})

        return res
