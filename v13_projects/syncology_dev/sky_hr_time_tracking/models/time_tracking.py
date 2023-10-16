from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import calendar
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import pytz
import math

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


class TimeTracking(models.Model):
    _name = 'time.tracking'

    _inherit = ['mail.thread']

    _description = 'Time Tracking'

    @api.depends('employee_id.first_name_arabic', 'employee_id.middle_name_arabic', 'employee_id.last_name_arabic', 'employee_id.fourth_name_arabic')
    def _compute_employee_name_arabic(self):
        for tracking in self:
            tracking.employee_arabic_name = str(tracking.employee_id.first_name_arabic) + " " + str(tracking.employee_id.middle_name_arabic) + " " + str(tracking.employee_id.last_name_arabic) + " " + str(tracking.employee_id.fourth_name_arabic)

    name = fields.Char('Description')
    employee_id = fields.Many2one('hr.employee', 'Employee', ondelete='restrict')
    employee_arabic_name = fields.Char('Employee (Arabic)', compute="_compute_employee_name_arabic", tracking=True, store=True)
    parent_id = fields.Many2one('hr.employee', 'parent', related='employee_id.parent_id', store=True)
    department_id = fields.Many2one('hr.department', string='Department',related='employee_id.department_id', store=True)
    job_id = fields.Many2one('hr.job', string='Job', related='employee_id.job_id', store=True)
    schedule_id = fields.Many2one('resource.calendar', 'Schedule')
    month = fields.Selection([('1', 'January'),
                              ('2', 'February'),
                              ('3', 'March'),
                              ('4', 'April'),
                              ('5', 'May'),
                              ('6', 'June'),
                              ('7', 'July'),
                              ('8', 'August'),
                              ('9', 'September'),
                              ('10', 'October'),
                              ('11', 'November'),
                              ('12', 'December')], 'Month')
    year = fields.Integer('Year')
    month_year = fields.Char(string='Month-Year', compute='_compute_month_year', store=True)
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    tracking_line_ids = fields.One2many('time.tracking.line', 'tracking_id', 'Tracking Lines')
    notes = fields.Html('Notes')
    state = fields.Selection([('draft', 'Draft'), ('open', 'Open'),
                              ('close', 'Close')], 'State', default='draft')
    tracking_batch_id = fields.Many2one('time.tracking.batch', 'Batch')

    @api.onchange('month', 'year')
    def onchange_month_year(self):
        """
        This method will update start date and end date value
        -----------------------------------------------------
        @param self: object pointer
        """
        # 'start_date': date(batch.year, int(batch.month), 1),
        # 'end_date': date(batch.year, int(batch.month), month_cal[1])
        for tracking in self:
            if tracking.month and tracking.year:
                month = int(tracking.month)
                year = tracking.year
                month_cal = calendar.monthrange(year, month)
                tracking.write({'start_date': date(year, month, 1), 'end_date': date(year, month, month_cal[1])})

    def open_tacking(self):
        """
        This method is used to change state open
        -----------------------------------------
        @param self: object pointer
        """
        for tracking in self:
            tracking.state = 'open'

    def close_tacking(self):
        """
        This method is used to change state close
        -----------------------------------------
        @param self: object pointer
        """
        for tracking in self:
            tracking.state = 'close'

    @api.model
    def default_get(self, fields_lst):
        """
        Overridden default_get method to get the current month and year
        ---------------------------------------------------------------
        @param self: object pointer
        @param fields_lst: List of fields which has default value
        """
        res = super(TimeTracking, self).default_get(fields_lst)
        cr_dt = fields.Date.today()
        res['month'] = str(cr_dt.month)
        res['year'] = cr_dt.year
        return res

    @api.onchange('employee_id')
    def onchange_emp(self):
        """
        Onchange method to calculate the Schedule of the Resource
        ---------------------------------------------------------
        @param self: object pointer
        """
        for rec in self:
            rec.schedule_id = False
            if rec.employee_id:
                rec.schedule_id = rec.employee_id.resource_calendar_id.id

    @api.depends('month', 'year')
    def _compute_month_year(self):
        """
        This method is used to set the description of the tracking
        ----------------------------------------------------------
        @param self: object pointer
        """
        for rec in self:
            rec.month_year = month_dict[rec.month] + '-' + str(rec.year)

    def generate_tracking(self):
        """
        This is a method which generates the complete time tracking for the Employees
        """
        tt_line_obj = self.env['time.tracking.line']
        for rec in self:
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
            # Generate Lines of Employee Tracking for the Month and Year
            month = int(rec.month)
            month_cal = calendar.monthrange(rec.year, month)
            first_day = date(rec.year, month, 1)
            last_day = date(rec.year, month, month_cal[1])
            rec.start_date = first_day
            rec.end_date = last_day
            cr_dt = first_day
            while cr_dt <= last_day:
                wo = False
                vals = {
                    'date': cr_dt,
                    'day': str(cr_dt.weekday()),
                    'tracking_id': rec.id,
                }
                # Check whether it's a Week off or not
                if str(cr_dt.weekday()) in week_off_dict.keys():
                    week_number = (cr_dt.day - 1) // 7 + 1
                    if week_number in week_off_dict[str(cr_dt.weekday())]:
                        wo = True
                if wo:
                    # If Week Off mention Week Off
                    vals.update({
                        'name': 'Week - Off',
                        'week_off': True
                    })
                else:
                    if str(cr_dt.weekday()) not in schedule_dict.keys():
                        raise ValidationError(_('Kindly configure weekoffs for the days when employees will not work!'))
                    # If working day add start and end time, break hours and working hours
                    vals.update({
                        'planned_start_time': schedule_dict[str(cr_dt.weekday())]['start_time'],
                        'planned_end_time': schedule_dict[str(cr_dt.weekday())]['end_time'],
                        'planned_break_hours': schedule_dict[str(cr_dt.weekday())]['break_hours'],
                        'planned_hours': schedule_dict[str(cr_dt.weekday())]['working_hours']
                    })
                # Create Tracking Line
                tt_line_obj.create(vals)
                # Go to Next Date
                cr_dt += relativedelta(days=1)
            rec.state = 'open'

    def compute_tracking(self):
        """
        This method will be used to update the tracking of each day for all employees
        -----------------------------------------------------------------------------
        @param self: object pointer
        """
        att_obj = self.env['hr.attendance']
        exc_obj = self.env['hr.time.exception']
        for rec in self:
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

    @api.model_create_multi
    def create(self, vals_lst):
        for vals in vals_lst:
            vals.update({
                'name': vals.get('name').lower()
            })
        return super(TimeTracking, self).create(vals_lst)

    def write(self, vals):
        if vals.get('name'):
            vals.update({
                'name': vals.get('name').lower()
            })
        res = super(TimeTracking, self).write(vals)
        return res

    @api.constrains('employee_id', 'month', 'year')
    def check_time_tracking(self):
        """
        This method is used to check the time tracking is already exist or not
        ----------------------------------------------------------------------
        @param self: object pointer
        """
        time_tracking = self.search_count([('employee_id', '=', self.employee_id.id), ('month', '=', self.month),
                                           ('year', '=', self.year)])
        if time_tracking > 1:
            raise ValidationError(_("Employee Time Tracking is already exist!!!"))


class TimeTrackingLine(models.Model):
    _name = 'time.tracking.line'

    _description = 'Time Tracking Line'

    _order = 'date'

    name = fields.Char('Description')
    date = fields.Date('Date')
    day = fields.Selection([('0', 'Monday'),
                            ('1', 'Tuesday'),
                            ('2', 'Wednesday'),
                            ('3', 'Thursday'),
                            ('4', 'Friday'),
                            ('5', 'Saturday'),
                            ('6', 'Sunday')], 'Weekday')
    planned_start_time = fields.Float('Planned Start Time', group_operator='avg')
    actual_start_time = fields.Float('Actual Start Time', group_operator='avg')
    diff_start_time = fields.Float(compute='_calc_diff_start_time', string='Late By', store=True, group_operator='avg')
    planned_end_time = fields.Float('Planned End Time', group_operator='avg')
    actual_end_time = fields.Float('Actual End Time', group_operator='avg')
    diff_end_time = fields.Float(compute='_calc_diff_end_time', string='Early By', store=True, group_operator='avg')
    planned_hours = fields.Float('Planned Hours')
    actual_hours = fields.Float(string='Actual Hours', compute='_calc_actual_hours', store=True)
    diff_working_hours = fields.Float(compute='_calc_diff_working_hours',
                                      string='Working Hours Difference',
                                      store=True,
                                      group_operator='avg')
    overtime_hours = fields.Float(compute='_calc_diff_working_hours',
                                  string='OverTime Hours',
                                  store=True)
    planned_break_hours = fields.Float('Planned Break Hours', group_operator='avg')
    actual_break_hours = fields.Float(string='Actual Break Hours', compute='_calc_actual_break_hours', store=True,
                                      group_operator='avg')
    diff_break_hours = fields.Float(compute='_calc_diff_break_hours', string='Break Hours Difference', store=True,
                                    group_operator='avg')
    attendance_ids = fields.One2many('hr.attendance', 'tracking_line_id', 'Attendances')
    present = fields.Boolean('Present?', compute='_calc_presence', store=True)
    tracking_id = fields.Many2one('time.tracking', 'Tracking')
    employee_id = fields.Many2one('hr.employee', related='tracking_id.employee_id',
                                  string='Employee', store=True)
    week_off = fields.Boolean('Week Off')
    exception_ids = fields.One2many('hr.time.exception', 'tracking_line_id', 'Exceptions')
    exception_hours = fields.Float('Exception Hours', compute='_calc_exception_hours', store=True)
    lock = fields.Boolean('lock')

    def export_data(self, fields_to_export):
        """ Override to change the float to time """
        index = range(len(fields_to_export))
        fields_name = dict(zip(fields_to_export, index))
        res = super(TimeTrackingLine, self).export_data(fields_to_export)
        for index, val in enumerate(res['datas']):
            if fields_name.get('actual_start_time'):
                field1index = fields_name.get('actual_start_time')
                fhours = float(res['datas'][index][field1index])
                res['datas'][index][field1index] = "%02d:%02d" % (fhours, abs(round(math.modf(fhours)[0] * 60)))
            if fields_name.get('planned_start_time'):
                field1index = fields_name.get('planned_start_time')
                fhours = float(res['datas'][index][field1index])
                res['datas'][index][field1index] = "%02d:%02d" % (fhours, abs(round(math.modf(fhours)[0] * 60)))
            if fields_name.get('planned_end_time'):
                field1index = fields_name.get('planned_end_time')
                fhours = float(res['datas'][index][field1index])
                res['datas'][index][field1index] = "%02d:%02d" % (fhours, abs(round(math.modf(fhours)[0] * 60)))
            if fields_name.get('actual_end_time'):
                field1index = fields_name.get('actual_end_time')
                fhours = float(res['datas'][index][field1index])
                res['datas'][index][field1index] = "%02d:%02d" % (fhours, abs(round(math.modf(fhours)[0] * 60)))
            if fields_name.get('planned_hours'):
                field1index = fields_name.get('planned_hours')
                fhours = float(res['datas'][index][field1index])
                res['datas'][index][field1index] = "%02d:%02d" % (fhours, abs(round(math.modf(fhours)[0] * 60)))
            if fields_name.get('diff_start_time'):
                field1index = fields_name.get('diff_start_time')
                fhours = float(res['datas'][index][field1index])
                res['datas'][index][field1index] = "%02d:%02d" % (fhours, abs(round(math.modf(fhours)[0] * 60)))
            if fields_name.get('diff_end_time'):
                field1index = fields_name.get('diff_end_time')
                fhours = float(res['datas'][index][field1index])
                res['datas'][index][field1index] = "%02d:%02d" % (fhours, abs(round(math.modf(fhours)[0] * 60)))
            if fields_name.get('actual_hours'):
                field1index = fields_name.get('actual_hours')
                fhours = float(res['datas'][index][field1index])
                res['datas'][index][field1index] = "%02d:%02d" % (fhours, abs(round(math.modf(fhours)[0] * 60)))
            if fields_name.get('diff_working_hours'):
                field1index = fields_name.get('diff_working_hours')
                fhours = float(res['datas'][index][field1index])
                res['datas'][index][field1index] = "%02d:%02d" % (fhours, abs(round(math.modf(fhours)[0] * 60)))
            if fields_name.get('overtime_hours'):
                field1index = fields_name.get('overtime_hours')
                fhours = float(res['datas'][index][field1index])
                res['datas'][index][field1index] = "%02d:%02d" % (fhours, abs(round(math.modf(fhours)[0] * 60)))
        return res


    @api.depends('planned_start_time', 'actual_start_time')
    def _calc_diff_start_time(self):
        """
        This method is used to calculate the difference between planned and actual start time
        -------------------------------------------------------------------------------------
        @param self: object pointer
        """
        for rec in self:
            rec.diff_start_time = 0.0
            if rec.planned_start_time and rec.actual_start_time:
                diff_start_time = rec.actual_start_time - rec.planned_start_time
                if diff_start_time > 0.0:
                    rec.diff_start_time = diff_start_time

    @api.depends('planned_end_time', 'actual_end_time')
    def _calc_diff_end_time(self):
        """
        This method is used to calculate the difference between planned and actual end time
        -----------------------------------------------------------------------------------
        @param self: object pointer
        """
        for rec in self:
            rec.diff_end_time = 0.0
            if rec.planned_end_time and rec.actual_end_time:
                diff_end_time = rec.planned_end_time - rec.actual_end_time
                if diff_end_time > 0.0:
                    rec.diff_end_time = diff_end_time

    @api.depends('planned_start_time', 'planned_end_time')
    def _calc_planned_hours(self):
        """
        This method is used to calculate Planned Working Hours
        ------------------------------------------------------
        @param self: object pointer
        """
        for rec in self:
            rec.planned_hours = rec.planned_end_time - rec.planned_start_time - rec.planned_break_hours

    @api.depends('attendance_ids')
    def _calc_actual_hours(self):
        """
        This method is used to calculate Actual Working Hours
        -----------------------------------------------------
        @param self: object pointer
        """
        for rec in self:
            w_hours = 0
            for att in rec.attendance_ids:
                w_hours += att.worked_hours
            rec.actual_hours = w_hours

    @api.depends('planned_start_time', 'planned_end_time', 'actual_start_time',
                 'actual_end_time', 'planned_hours', 'actual_hours')
    def _calc_diff_working_hours(self):
        """
        This method is used to calculate the working hours difference
        -------------------------------------------------------------
        """
        for rec in self:
            rec.overtime_hours = 0.0
            rec.diff_working_hours = rec.planned_hours - rec.actual_hours
            if rec.diff_working_hours < 0:
                rec.overtime_hours = abs(rec.planned_hours - rec.actual_hours)

    @api.depends('attendance_ids')
    def _calc_actual_break_hours(self):
        """
        This method is used to calculate Actual Break Hours
        ---------------------------------------------------
        @param self: object pointer
        """
        for rec in self:
            first_sign_in = False
            last_sign_out = False
            actual_break_hours = 0.0
            for att in rec.attendance_ids:
                if not first_sign_in or (first_sign_in > att.check_in):
                    first_sign_in = att.check_in
                if not last_sign_out or (att.check_out and (last_sign_out < att.check_out)):
                    last_sign_out = att.check_out
                if last_sign_out:
                    diff = last_sign_out - first_sign_in
                    diff_hours = diff.seconds / 3600.0
                    actual_break_hours = diff_hours - rec.actual_hours
            rec.actual_break_hours = actual_break_hours

    @api.depends('attendance_ids', 'planned_break_hours')
    def _calc_diff_break_hours(self):
        """
        This method is used to calcualte the difference in Break Hours
        --------------------------------------------------------------
        @param self: object pointer
        """
        for rec in self:
            rec.diff_break_hours = rec.planned_break_hours - rec.actual_break_hours

    @api.depends('exception_ids')
    def _calc_exception_hours(self):
        """
        This method is used to calculate the exception hours
        ----------------------------------------------------
        @param self: object pointer
        """
        for rec in self:
            exc_hours = 0.0
            for exc in rec.exception_ids:
                if exc.state == 'approved':
                    exc_hours += exc.duration
            rec.exception_hours = exc_hours

    @api.depends('attendance_ids')
    def _calc_presence(self):
        """
        This will check whether the employee is present today or not.
        -------------------------------------------------------------
        @param self: object pointer
        """
        for rec in self:
            rec.present = rec.attendance_ids.ids and True or False


class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    week_off_ids = fields.One2many('resource.calendar.weekoff', 'resource_id', 'Week Offs')


class ResourceCalendarAttendance(models.Model):
    _inherit = 'resource.calendar.attendance'

    break_hours = fields.Float('Break Hours')
    total_hours = fields.Float(string='Total Hours', compute='_calc_total_hours', store=True)
    working_hours = fields.Float(string='Working Hours', compute='_calc_working_hours', store=True)

    _sql_constraints = [('unique_week_day', 'unique(calendar_id,dayofweek)', 'You can set only unique week day!')]

    @api.depends('hour_from', 'hour_to')
    def _calc_total_hours(self):
        """
        A method to calculate the Total Hours
        -------------------------------------
        @param self: object pointer
        """
        for rec in self:
            rec.total_hours = rec.hour_to - rec.hour_from

    @api.depends('total_hours', 'break_hours')
    def _calc_working_hours(self):
        """
        A method to calculate the Working Hours
        ---------------------------------------
        @param self: object pointer
        """
        for rec in self:
            rec.working_hours = rec.total_hours - rec.break_hours


class ResourceCalendarWeekOff(models.Model):
    _name = 'resource.calendar.weekoff'

    _description = 'Resource Calendar WeekOff'

    resource_id = fields.Many2one('resource.calendar', 'Work Schedule')
    week_day = fields.Selection([('0', 'Monday'),
                                 ('1', 'Tuesday'),
                                 ('2', 'Wednesday'),
                                 ('3', 'Thursday'),
                                 ('4', 'Friday'),
                                 ('5', 'Saturday'),
                                 ('6', 'Sunday')], 'Weekday')
    week_1 = fields.Boolean('1st Week')
    week_2 = fields.Boolean('2nd Week')
    week_3 = fields.Boolean('3rd Week')
    week_4 = fields.Boolean('4th Week')
    week_5 = fields.Boolean('5th Week')


class TimeTrackingBatch(models.Model):
    _name = 'time.tracking.batch'
    _description = 'Time Tracking Batch'

    name = fields.Char('Description')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)
    department_ids = fields.Many2many('hr.department', string='Departments')
    employee_ids = fields.Many2many('hr.employee', string='Employees')
    state = fields.Selection([('draft', 'Draft'),
                              ('in_progress', 'In Progress'),
                              ('done', 'Completed')], 'State', default='draft')
    month = fields.Selection([('1', 'January'),
                              ('2', 'February'),
                              ('3', 'March'),
                              ('4', 'April'),
                              ('5', 'May'),
                              ('6', 'June'),
                              ('7', 'July'),
                              ('8', 'August'),
                              ('9', 'September'),
                              ('10', 'October'),
                              ('11', 'November'),
                              ('12', 'December')], 'Month')
    year = fields.Integer('Year')
    month_year = fields.Char(string='Month-Year', compute='_compute_month_year', store=True)
    tracking_ids = fields.One2many('time.tracking', 'tracking_batch_id', 'Trackings')

    @api.depends('month', 'year')
    def _compute_month_year(self):
        """
        This method is used to set the description of the batch
        -------------------------------------------------------
        @param self: object pointer
        """
        for batch in self:
            batch.month_year = month_dict[batch.month] + '-' + str(batch.year)

    @api.onchange('company_id')
    def onchange_company(self):
        """
        This method is used to add filters on the departments and employees of the selected companies.
        ----------------------------------------------------------------------------------------------
        @param self: object pointer
        """
        for batch in self:
            res = {'domain':
                       {'department_ids': [],
                        'employee_ids': []}}
            if batch.company_id:
                res = {'domain':
                           {'department_ids':
                                [('comapny_id', '=', batch.company_id.id)],
                            'employee_ids':
                                [('comapny_id', '=', batch.company_id.id)]}}
            return res

    @api.onchange('department_ids')
    def onchange_company(self):
        """
        This method is used to add filters on the employees of the selected departments.
        --------------------------------------------------------------------------------
        @param self: object pointer
        """
        for batch in self:
            res = {'domain': {'employee_ids': []}}
            if batch.department_ids:
                res = {'domain':
                           {'employee_ids':
                                [('department_id', 'in', batch.department_ids.ids)]}}
            return res

    def generate_batch_tracking(self):
        """
        This method is used to generate time tracking for all the employees as per selection
        ------------------------------------------------------------------------------------
        @param self: object pointer
        """
        emp_obj = self.env['hr.employee']
        tracking_obj = self.env['time.tracking']
        for batch in self:
            employees = batch.employee_ids
            if not employees:
                if not batch.department_ids:
                    employees = emp_obj.search([('company_id', '=', batch.company_id.id)])
                else:
                    employees = emp_obj.search([('department_id', 'in', batch.department_ids.ids)])
            for employee in employees:
                time_tracking = tracking_obj.search([('employee_id', '=', employee.id), ('month', '=', batch.month),
                                                     ('year', '=', batch.year)])
                if not time_tracking:
                    # Create Tracking for Employee
                    month_cal = calendar.monthrange(batch.year, int(batch.month))
                    tracking_vals = {
                        'name': month_dict[batch.month] + '-' + str(batch.year) + ' : ' + employee.name,
                        'month': batch.month,
                        'year': batch.year,
                        'employee_id': employee.id,
                        'schedule_id': employee.resource_calendar_id.id,
                        'tracking_batch_id': batch.id,
                        'start_date': date(batch.year, int(batch.month), 1),
                        'end_date': date(batch.year, int(batch.month), month_cal[1]),
                        'state': 'open'
                    }
                    tracking_obj.create(tracking_vals)
            batch.state = 'in_progress'

    def complete_batch(self):
        """
        This method is used to complete the batch post which no updates can be made.
        ----------------------------------------------------------------------------
        @param self: object pointer
        """
        for batch in self:
            batch.tracking_ids.close_tacking()
            batch.state = 'done'

    def reset_batch(self):
        """
        This method is used to reset the batch
        --------------------------------------
        @param self: object pointer
        """
        for batch in self:
            batch.tracking_ids.unlink()
            batch.state = 'draft'

    def compute_batch(self):
        """
        This method will compute the tracking of the batch from attendance of the employees
        -----------------------------------------------------------------------------------
        @param self: object pointer
        """
        for batch in self:
            batch.tracking_ids.compute_tracking()

    @api.model
    def _create_time_tracking(self):
        """
        This method will create time tracking batch every month for all the employees of the company
        --------------------------------------------------------------------------------------------
        @param self: object pointer
        """
        comp_obj = self.env['res.company']
        companies = comp_obj.search([])
        cr_dt = fields.Date.today()
        # Create Time Tracking batches
        for company in companies:
            batch_vals = {
                'name': 'Time Tracking for ' + month_dict[str(cr_dt.month)] + ' ' + company.name,
                'month': str(cr_dt.month),
                'year': cr_dt.year,
                'company_id': company.id,
            }
            # Create Batch
            batch = self.create(batch_vals)
            # Generate Batch
            batch.generate_batch_tracking()


class TimeException(models.Model):
    _name = 'hr.time.exception'
    _description = 'Time Exception'
    _inherit = ['mail.thread']

    name = fields.Char('Reason')
    employee_id = fields.Many2one('hr.employee', 'Employee')
    date = fields.Date('Date', default=fields.Date.today())
    start_time = fields.Float('Start Time')
    end_time = fields.Float('End Time')
    duration = fields.Float('Duration', compute='_calculate_duration', store=True)
    notes = fields.Html('Notes')
    state = fields.Selection([('draft', 'Draft'),
                              ('confirmed', 'Applied'),
                              ('validated', 'Validated'),
                              ('approved', 'Approved'),
                              ('rejected', 'Rejected'),
                              ('canceled', 'Canceled')], 'State', default='draft')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id.id)
    tracking_line_id = fields.Many2one('time.tracking.line', 'Tracking Line')

    @api.depends('start_time', 'end_time')
    def _calculate_duration(self):
        """
        This method is used to calculate the duration
        ---------------------------------------------
        @param self: object pointer
        """
        for exc in self:
            exc.duration = exc.end_time - exc.start_time
            # If it was a night shift
            if exc.duration < 0.0:
                exc.duration += 24.0

    def confirm_exception(self):
        """
        This method will be used when the exception is applied by the employee
        ----------------------------------------------------------------------
        @param self: object pointer
        """
        for exc in self:
            exc.state = 'confirmed'

    def validate_exception(self):
        """
        This method will be used when the exception is validated by the Manager
        -----------------------------------------------------------------------
        @param self: object pointer
        """
        for exc in self:
            exc.state = 'validated'

    def approve_exception(self):
        """
        This method will be used when the exception is approved by the Higher Authority
        -------------------------------------------------------------------------------
        @param self: object pointer
        """
        for exc in self:
            exc.state = 'approved'

    def reject_exception(self):
        """
        This method will be used when the exception is rejected by the Manager / Higher Authority
        -----------------------------------------------------------------------------------------
        @param self: object pointer
        """
        for exc in self:
            exc.state = 'rejected'

    def cancel_exception(self):
        """
        This method will be used when the exception is canceled by the Employee
        -----------------------------------------------------------------------
        @param self: object pointer
        """
        for exc in self:
            exc.state = 'canceled'

    def draft_exception(self):
        """
        This method will be used when the exception is set to draft by the Employee
        ---------------------------------------------------------------------------
        @param self: object pointer
        """
        for exc in self:
            exc.state = 'draft'
