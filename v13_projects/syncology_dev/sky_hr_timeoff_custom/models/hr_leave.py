from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError ,AccessError
import calendar
from datetime import date
from pytz import timezone, UTC
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY
import math

class Leave(models.Model):
    _inherit = 'hr.leave'
    _description = 'Leave'

    @api.depends('employee_id.first_name_arabic', 'employee_id.middle_name_arabic', 'employee_id.last_name_arabic', 'employee_id.fourth_name_arabic')
    def _compute_employee_name_arabic(self):
        for request in self:
            request.employee_arabic_name = str(request.employee_id.first_name_arabic) + " " + str(request.employee_id.middle_name_arabic) + " " + str(request.employee_id.last_name_arabic) + " " + str(request.employee_id.fourth_name_arabic)

    employee_id = fields.Many2one('hr.employee', 'Employee')
    employee_arabic_name = fields.Char('Employee (Arabic)', compute="_compute_employee_name_arabic", tracking=True, store=True)
    leave_type = fields.Selection([('vacation', 'Vacation'),
                                   ('leave', 'Leave')], 'Leave Type')
    rejection = fields.Char('Rejection Reason')
    leave_paycut = fields.Float('Leave Paycut')
    vacation_paycut = fields.Float('Vacation Paycut')
    penalty_id = fields.Many2one('hr.penalty.type', 'Penalty')
    penalty_value = fields.Integer('Value')
    penalty_unit = fields.Selection([('days', 'Days'), ('hours', 'Hours'), ('minutes', 'Minutes')], 'Unit')
    current_yearly_balance = fields.Integer('Current Yearly Balance')
    yearly_request_made = fields.Integer('Yearly Requests Made')
    monthly_allowance = fields.Integer('Monthly Allowance')
    monthly_request_made = fields.Integer('Monthly Requests Made')
    start_time = fields.Float('Start Time')
    end_time = fields.Float('End Time')
    number_of_days = fields.Integer(
        'Duration (Days)', copy=False, tracking=True,
        help='Number of days of the time off request. Used in the calculation. To manually correct the duration, use this field.')
    number_of_days_display = fields.Integer(
        'Duration in days', compute='_compute_number_of_days_display', readonly=True,
        help='Number of days of the time off request according to your working schedule. Used for interface.')
    unpaid = fields.Boolean('Unpaid', related='holiday_status_id.unpaid')
    lock = fields.Boolean('Lock')
    gate_start_time = fields.Float('Gate Start Time')
    gate_end_time = fields.Float('Gate End Time')
    leave_period = fields.Selection([('morning_leave', 'Morning Leave'),
                                     ('evening_leave', 'Evening Leave')], 'Leave Period')
    emp_parent_id = fields.Many2one('hr.employee', 'Manager', related='employee_id.parent_id', store=True)
    job_id = fields.Many2one('hr.job', string='Job', related='employee_id.job_id', store=True)

    @api.depends('start_time', 'end_time', 'number_of_days')
    def _compute_number_of_hours_display(self):
        for holiday in self:
            if self._context.get('default_leave_type') == 'leave':
                if holiday.start_time and holiday.end_time:
                    holiday.number_of_hours_display = math.ceil(holiday.end_time - holiday.start_time)
                else:
                    holiday.number_of_hours_display = 0
            else:
                calendar = holiday._get_calendar()
                if holiday.date_from and holiday.date_to:
                    # Take attendances into account, in case the leave validated
                    # Otherwise, this will result into number_of_hours = 0
                    # and number_of_hours_display = 0 or (#day * calendar.hours_per_day),
                    # which could be wrong if the employee doesn't work the same number
                    # hours each day
                    if holiday.state == 'validate':
                        start_dt = holiday.date_from
                        end_dt = holiday.date_to
                        if not start_dt.tzinfo:
                            start_dt = start_dt.replace(tzinfo=UTC)
                        if not end_dt.tzinfo:
                            end_dt = end_dt.replace(tzinfo=UTC)
                        resource = holiday.employee_id.resource_id
                        intervals = calendar._attendance_intervals_batch(start_dt, end_dt, resource)[resource.id] \
                                    - calendar._leave_intervals_batch(start_dt, end_dt, None)[
                                        False]  # Substract Global Leaves
                        number_of_hours = sum((stop - start).total_seconds() / 3600 for start, stop, dummy in intervals)
                    else:
                        number_of_hours = \
                        holiday._get_number_of_days(holiday.date_from, holiday.date_to, holiday.employee_id.id)['hours']
                    holiday.number_of_hours_display = number_of_hours or (
                                holiday.number_of_days * (calendar.hours_per_day or HOURS_PER_DAY))
                else:
                    holiday.number_of_hours_display = 0


    @api.model
    def default_get(self, fields):
        res = super(Leave, self).default_get(fields)
        if res.get('holiday_status_id', False):
            del res['holiday_status_id']

        res.update({'request_date_from': date.today(), 'request_date_to': date.today()})
        return res

    def action_approve(self):
        for record in self:
            if record.holiday_status_id.validation_type == 'manager':
                raise_flag = True
                if self.env.user.has_group('hr_holidays.group_hr_holidays_responsible') or self.env.user.has_group('hr_holidays.group_hr_holidays_user'):
                    raise_flag = False
                if raise_flag:
                    raise UserError(_('Logged in user cannot approve this leave/vacation. User must have (Responsible) rights.'))
            if record.holiday_status_id.validation_type == 'hr':
                raise_flag = True
                if self.env.user.has_group('sky_hr_timeoff_custom.grp_timeoff_officer'):
                    raise_flag = False
                if raise_flag:
                    raise UserError(_('Logged in user cannot approve this leave/vacation. User must have (TimeOff Officer) rights.'))
            if record.holiday_status_id.validation_type == 'both':
                raise_flag = True
                if self.env.user.has_group('hr_holidays.group_hr_holidays_responsible') or self.env.user.has_group('hr_holidays.group_hr_holidays_user') or self.env.user.has_group('sky_hr_timeoff_custom.grp_timeoff_officer'):
                    raise_flag = False
                if raise_flag:
                    raise UserError(_('An officer or timeoff responsible can only approve the request.'))

            # if unpaid leave then create Penalty
            if record.holiday_status_id and record.holiday_status_id.unpaid:
                if not record.penalty_id:
                    raise ValidationError(_("Please Select Penalty..!"))
                if not record.penalty_value or not record.penalty_unit:
                    raise ValidationError(_("Please Select Value of Penalty Value and Unit"))
        return super(Leave, self).action_approve()

    def action_approve1(self):
        for record in self:
            if record.holiday_status_id.validation_type in ['hr', 'both']:
                raise_flag = True
                if self.env.user.has_group('sky_hr_timeoff_custom.grp_timeoff_officer'):
                    raise_flag = False
                if raise_flag:
                    raise UserError(_('Logged in user cannot approve this leave/vacation. User must have (TimeOff Officer) rights.'))
        # if validation_type == 'both': this method is the first approval approval
        # if validation_type != 'both': this method calls action_validate() below
        if any(holiday.state != 'confirm' for holiday in self):
            raise UserError(_('Time off request must be confirmed ("To Approve") in order to approve it.'))

        current_employee = self.env.user.employee_id
        self.filtered(lambda hol: hol.validation_type == 'both').write({'state': 'validate1', 'first_approver_id': current_employee.id})


        # Post a second message, more verbose than the tracking message
        for holiday in self.filtered(lambda holiday: holiday.employee_id.user_id):
            holiday.message_post(
                body=_('Your %s planned on %s has been accepted') % (holiday.holiday_status_id.display_name, holiday.date_from),
                partner_ids=holiday.employee_id.user_id.partner_id.ids)

        self.filtered(lambda hol: not hol.validation_type == 'both').action_validate()
        if not self.env.context.get('leave_fast_create'):
            self.activity_update()
        return True

    def action_reject(self):
        return {
            'name': _("Reject Request"),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'reject.request.wizard',
            'target': 'new',
        }

    @api.onchange('date_from')
    def _onchange_leave_dates(self):
        super(Leave, self)._onchange_leave_dates()
        if self.leave_type == 'leave':
            if self.date_from:
                self.number_of_days = 1
            else:
                self.number_of_days = 1

    @api.onchange('request_date_from')
    def onchange_request_date_to(self):
        if self.leave_type == 'leave':
            for holiday in self:
                holiday.request_date_to = holiday.request_date_from

    @api.onchange('employee_id', 'holiday_status_id', 'request_date_from')
    def onchange_leave_monthly_allowance(self):
        """This will update Yearly and Monthly Leave/Vacation Request,Current Leave/Vacation Balance and monthly
        allowance """
        leave_request_obj = self.env['hr.leave']
        for holiday in self:
            if not holiday.holiday_status_id.unpaid:
                month_range = calendar.monthrange(holiday.request_date_from.year, holiday.request_date_from.month)
                st_dt = date(holiday.request_date_from.year, holiday.request_date_from.month, 1)
                en_dt = date(holiday.request_date_from.year, holiday.request_date_from.month, month_range[1])
                year_st_dt = date(holiday.request_date_from.year, 1, 1)
                year_en_dt = date(holiday.request_date_from.year, 12, 31)

                if holiday.leave_type == 'vacation':

                    vacation_bal_line = self.env['employee.vacation.balance.by.type'].search([
                        ('employee_id', '=', holiday.employee_id.id),
                        ('leave_type_id', '=', holiday.holiday_status_id.id)
                    ], limit=1)
                    holiday.current_yearly_balance = vacation_bal_line.vacation_balance
                    holiday.monthly_allowance = vacation_bal_line.vacation_monthly_allowance

                    vacations_req_monthly = leave_request_obj.search(
                        [('employee_id', '=', holiday.employee_id.id),
                         ('state', 'in', ('validate', 'validate1')),
                         ('leave_type', '=', 'vacation'),
                         ('holiday_status_id', '=', holiday.holiday_status_id.id),
                         ('request_date_from', '>=', st_dt),
                         ('request_date_from', '<=', en_dt)])
                    vacation_days_monthly = sum(vacations_req_monthly.mapped('number_of_days'))

                    vacations_req_yearly = leave_request_obj.search([
                        ('employee_id', '=', holiday.employee_id.id),
                        ('state', 'in', ('validate', 'validate1')),
                        ('leave_type', '=', 'vacation'),
                        ('holiday_status_id', '=', holiday.holiday_status_id.id),
                        ('request_date_from', '>=', year_st_dt),
                        ('request_date_from', '<=', year_en_dt)])
                    vacation_days_yearly = sum(vacations_req_yearly.mapped('number_of_days'))

                    holiday.yearly_request_made = vacation_days_yearly
                    holiday.monthly_request_made = vacation_days_monthly

                if holiday.leave_type == 'leave':

                    leave_bal_line = self.env['employee.leave.balance.by.type'].search([
                        ('employee_id', '=', holiday.employee_id.id),
                        ('leave_type_id', '=', holiday.holiday_status_id.id)
                    ], limit=1)
                    holiday.current_yearly_balance = leave_bal_line.leave_balance
                    holiday.monthly_allowance = leave_bal_line.leave_monthly_allowance

                    leave_req_monthly = leave_request_obj.search(
                        [('employee_id', '=', holiday.employee_id.id),
                         ('state', 'in', ('validate', 'validate1')),
                         ('leave_type', '=', 'leave'),
                         ('holiday_status_id', '=', holiday.holiday_status_id.id),
                         ('request_date_from', '>=', st_dt),
                         ('request_date_from', '<=', en_dt)])
                    leave_monthly = sum(leave_req_monthly.mapped('number_of_hours_display'))

                    leave_req_yearly = leave_request_obj.search([
                        ('employee_id', '=', holiday.employee_id.id),
                        ('state', 'in', ('validate', 'validate1')),
                        ('leave_type', '=', 'leave'),
                        ('holiday_status_id', '=', holiday.holiday_status_id.id),
                        ('request_date_from', '>=', year_st_dt),
                        ('request_date_from', '<=', year_en_dt)])
                    leaves_yearly = sum(leave_req_yearly.mapped('number_of_hours_display'))

                    holiday.yearly_request_made = leaves_yearly
                    holiday.monthly_request_made = leave_monthly

    @api.constrains('number_of_days', 'request_date_from', 'request_date_to', 'start_time', 'end_time')
    def _check_holidays(self):
        """
        The overridden method to check the new rules of leaves and vacations
        --------------------------------------------------------------------
        @param self: object pointer
        """
        emp_lv_bl_obj = self.env['employee.leave.balance.by.type']
        emp_vac_bl_obj = self.env['employee.vacation.balance.by.type']
        for holiday in self:
            month_range = calendar.monthrange(holiday.request_date_from.year, holiday.request_date_from.month)
            st_dt = date(holiday.request_date_from.year, holiday.request_date_from.month, 1)
            en_dt = date(holiday.request_date_from.year, holiday.request_date_from.month, month_range[1])
            if holiday.leave_type == 'leave':
                # Leaves
                leaves = self.search([
                    ('employee_id', '=', holiday.employee_id.id),
                    ('state', 'in', ('validate', 'validate1')),
                    ('leave_type', '=', 'leave'),
                    ('request_date_from', '>=', st_dt),
                    ('request_date_from', '<=', en_dt),
                    ('holiday_status_id', '=', holiday.holiday_status_id.id),
                    ('holiday_status_id.unpaid', '=', False)
                ])
                leave_hours = sum(leaves.mapped('number_of_hours_display'))
                total_leave = leave_hours + holiday.number_of_hours_display
                if not holiday.holiday_status_id.unpaid:
                    leave_type_monthly_allowance = emp_lv_bl_obj.search([
                        ('employee_id', '=', holiday.employee_id.id),
                        ('leave_type_id', '=', holiday.holiday_status_id.id)
                    ], limit=1)
                    monthly_allowance_leave = leave_type_monthly_allowance.ids and leave_type_monthly_allowance.leave_monthly_allowance or 0.0
                    monthly_total_leave = holiday.monthly_request_made + holiday.number_of_hours_display
                    if holiday.current_yearly_balance < total_leave:
                        raise ValidationError(_('You do not have enough leaves balance check your leave balance!!!'))
                    elif monthly_allowance_leave < monthly_total_leave:
                        raise ValidationError(
                            _("You can take maximum {0} hours of leave in a  month!!!".format(str(monthly_allowance_leave))))

            # Vacation
            if holiday.leave_type == 'vacation':
                vacation = holiday.search([
                    ('employee_id', '=', holiday.employee_id.id),
                    ('state', 'in', ('validate', 'validate1')),
                    ('leave_type', '=', 'vacation'),
                    ('request_date_from', '>=', st_dt),
                    ('request_date_from', '<=', en_dt),
                    ('holiday_status_id', '=', holiday.holiday_status_id.id),
                    ('holiday_status_id.unpaid', '=', False)
                ])
                vacation_days = sum(vacation.mapped('number_of_days'))
                total_vacation = vacation_days + holiday.number_of_days
                if not holiday.holiday_status_id.unpaid:
                    vaca_type_monthly_allowance = emp_vac_bl_obj.search([
                        ('employee_id', '=', holiday.employee_id.id),
                        ('leave_type_id', '=', holiday.holiday_status_id.id)
                    ], limit=1)
                    monthly_allowance_vacation = vaca_type_monthly_allowance.vacation_monthly_allowance
                    monthly_total_vacation = holiday.monthly_request_made + holiday.number_of_days
                    if holiday.current_yearly_balance < total_vacation:
                        raise ValidationError(
                            _('You do not have enough vacation balance check your vacation balance!!!'))
                    elif monthly_allowance_vacation < monthly_total_vacation:
                        raise ValidationError(
                            _("You can take maximum {0} days of vacation for month!!!".format(str(monthly_allowance_vacation))))

    @api.constrains('start_time', 'end_time')
    def check_start_end_date(self):
        """
        This will check whether the start time is earlier than the end time or not
        ---------------------------------------------------------------------------
        @param self: object pointer
        """
        if not 0.0 <= self.start_time < 23.99:
            raise ValidationError(_('Start time must be between 00:00 to 23:59!!!'))

        if not 0.0 <= self.end_time < 23.99:
            raise ValidationError(_('End time must be between 00:00 to 23:59!!!'))

        if self.end_time < self.start_time:
            raise ValidationError(_('Start Time must be prior to End Time!'))

    def name_get(self):
        res = []
        for leave in self:
            if self.env.context.get('short_name'):
                if leave.leave_type_request_unit == 'hour':
                    res.append((leave.id, _("%s : %d hours") % (
                        leave.name or leave.holiday_status_id.name, leave.number_of_hours_display)))
                else:
                    res.append((leave.id,
                                _("%s : %d days") % (leave.name or leave.holiday_status_id.name, leave.number_of_days)))
            else:
                if leave.holiday_type == 'company':
                    target = leave.mode_company_id.name
                elif leave.holiday_type == 'department':
                    target = leave.department_id.name
                elif leave.holiday_type == 'category':
                    target = leave.category_id.name
                else:
                    target = leave.employee_id.name
                if leave.leave_type_request_unit == 'hour':
                    res.append(
                        (leave.id,
                         _("%s on %s : %d hours") %
                         (target, leave.holiday_status_id.name, leave.number_of_hours_display))
                    )
                else:
                    res.append(
                        (leave.id,
                         _("%s on %s: %d days") %
                         (target, leave.holiday_status_id.name, leave.number_of_days))
                    )
        return res

    def unlink(self):
        """
        Overridden unlink() method to restrict deletion of Approved Leaves
        ------------------------------------------------------------------
        @param self: object pointer
        :return:True
        """
        for leave in self:
            if leave.state not in ['draft', 'confirm']:
                raise UserError(_("You can not delete a leave which is approved!"))
        return super(Leave, self).unlink()

    def _check_double_validation_rules(self, employees, state):
        if self.user_has_groups('hr_holidays.group_hr_holidays_manager'):
            return

        is_leave_user = self.user_has_groups('hr_holidays.group_hr_holidays_user') or self.user_has_groups('sky_hr_timeoff_custom.grp_timeoff_officer')
        if state == 'validate1':
            employees = employees.filtered(lambda employee: employee.leave_manager_id != self.env.user)
            if employees and not is_leave_user:
                raise AccessError(_('You cannot first approve a leave for %s, because you are not his leave manager' % (employees[0].name,)))
        elif state == 'validate' and not is_leave_user:
            # Is probably handled via ir.rule
            raise AccessError(_('You don\'t have the rights to apply second approval on a leave request'))

    def action_validate(self):
        if self._context.get('button_validate'):
            raise_flag = True
            if self.env.user.has_group('hr_holidays.group_hr_holidays_responsible') or self.env.user.has_group('hr_holidays.group_hr_holidays_manager') or self.env.user.has_group('sky_hr_timeoff_custom.grp_timeoff_officer'):
                raise_flag = False
            if raise_flag:
                raise UserError(
                    _('Logged in user cannot approve this leave/vacation. User must have  (TimeOff Officer) rights.'))
        return super(Leave, self).action_validate()

    @api.model_create_multi
    def create(self,vals_lst):
        for vals in vals_lst:
            if 'validation_type' in vals:
                del vals['validation_type']
        res = super(Leave, self).create(vals_lst)
        res.state = 'draft'
        res.action_confirm()
        return res

    def write(self, vals):
        if 'validation_type' in vals:
            del vals['validation_type']
        return super().write(vals)

    def _get_responsible_for_approval(self):
        self.ensure_one()
        responsible = self.env['res.users'].browse(SUPERUSER_ID)

        if self.validation_type == 'manager' or (self.validation_type == 'both' and self.state == 'confirm'):
            if self.employee_id.leave_manager_id:
                responsible = self.employee_id.leave_manager_id
            elif self.employee_id.parent_id.user_id:
                responsible = self.employee_id.parent_id.user_id
        elif self.validation_type == 'hr' or (self.validation_type == 'both' and self.state == 'validate1'):
            if self.holiday_status_id.responsible_ids.ids:
                responsible = self.holiday_status_id.responsible_ids[0]
        return responsible
