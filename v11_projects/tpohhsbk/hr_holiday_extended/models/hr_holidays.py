# -*- coding: utf-8 -*-

import calendar
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class Holidays(models.Model):
    _inherit = "hr.holidays"

    date_from = fields.Date('Start Date', readonly=True, index=True,
                            copy=False,
                            states={'draft': [('readonly', False)],
                                    'confirm': [('readonly', False)]},
                            track_visibility='onchange')
    date_to = fields.Date('End Date', readonly=True, copy=False,
                          states={'draft': [('readonly', False)],
                                  'confirm': [('readonly', False)]},
                          track_visibility='onchange')
    carry_forwarded = fields.Boolean('Is Allocation Carry Forwarded?')
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)
    lapse_leave = fields.Boolean(string='Is Lapse Leave')
    carry_forward_lapse_leave = fields.Boolean(
        string='Carry Forwarded Lapse Leave')
    is_pro_rata_leave = fields.Boolean(default=False, string="Is Pro Rata Leave")
    is_leave_adjustment = fields.Boolean(string="Leave Adjustment",Copy=False)
    state = fields.Selection([
        ('draft', 'To Submit'),
        ('cancel', 'Cancelled'),
        ('confirm', 'To Approve'),
        ('refuse', 'Refused'),
        ('validate1', 'Second Approval'),
        ('validate', 'Approved'),
        ('encashed', 'Encashed')
    ], string='Status', readonly=True, track_visibility='onchange', copy=False,
        default='confirm')
    encashment_id = fields.Many2one('leave.encashment', string="Encashment")
    encash_amount = fields.Float("Encash Amount")
    lapse_leave_id = fields.Many2one('lapse.employee.leave', string="Lapse Leave",copy=False)
    

    @api.constrains('date_from', 'date_to','number_of_days_temp')
    def _check_date(self):
        for holiday in self:
            if holiday.lapse_leave_id and not self._context.get('lapse_leave'):
                raise ValidationError(_("You can't change leave duration."))

            domain = [
                ('date_from', '<=', holiday.date_to),
                ('date_to', '>=', holiday.date_from),
                ('employee_id', '=', holiday.employee_id.id),
                ('carry_forwarded', '=', holiday.carry_forwarded),
                ('id', '!=', holiday.id),
                ('type', '=', holiday.type),
                ('lapse_leave_id', '=', False),
                ('state', 'not in', ['cancel', 'refuse']),
            ]
            if holiday.type != 'remove':
                domain.append(('holiday_status_id', '=', holiday.holiday_status_id.id))

            nholidays = self.search_count(domain)
            if nholidays:
                raise ValidationError(_('You can not have 2 leaves that '
                                        'overlaps on same day!'))

    @api.multi
    def _prepare_holidays_meeting_values(self):
        """
         this method is override for create lapse leave calendar event.
        :return:
        """
        result = super(Holidays, self)._prepare_holidays_meeting_values()
        ctx = dict(self._context)
        if ctx.get('lapse_leave'):
            result.update({'start': datetime.now(), 'stop': datetime.now()})
        return result

    @api.multi
    def _create_resource_leave(self):
        """ This method will override for create entry in resource calendar
        leave object at the time of holidays validated """
        ctx = dict(self._context)
        if ctx.get('lapse_leave'):
            self.env['resource.calendar.leaves'].create({
                'name': self.name,
                'date_from': datetime.now(),
                'holiday_id': self.id,
                'date_to': datetime.now(),
                'resource_id': self.employee_id.resource_id.id,
                'calendar_id': self.employee_id.resource_calendar_id.id
            })
            return True
        else:
            return super(Holidays, self)._create_resource_leave()

    def _validate_leave_request(self):
        """ this method is override for stop creating
        holiday.calendar.event for lapse leave"""
        ctx = dict(self._context)
        if ctx.get('lapse_leave'):
            return True
        else:
            return super(Holidays, self)._validate_leave_request()

    def _get_number_of_days(self, date_from, date_to, employee_id):
        """ Returns a float equals to the timedelta between
         two dates given as string."""
        if self.type == 'remove':
            days_duration = 0.0
            if date_from and date_to:
                days_duration = (datetime.strptime(date_to, '%Y-%m-%d') - 
                                 datetime.strptime(date_from,
                                                   '%Y-%m-%d')).days + 1
            return days_duration

    @api.onchange('date_from')
    def _onchange_date_from(self):
        if self.type == 'remove':
            return super(Holidays, self)._onchange_date_from()

    @api.onchange('date_to')
    def _onchange_date_to(self):
        if self.type == 'remove':
            return super(Holidays, self)._onchange_date_to()

    @api.multi
    def action_refuse(self):
        """
        This method used for to refuse the leave and unlink the move which are created from lapse leave.
        """
        res =  super(Holidays, self).action_refuse()
        for holiday in self:
            if holiday.lapse_leave_id and holiday.type == 'remove':
                move_id = holiday.account_move_id.sudo()
                if move_id:
                    holiday.leave_amount = -move_id.amount
                    move_id.button_cancel()
                    move_id.line_ids.remove_move_reconcile()
                    move_id.with_context({'custom_move':True}).unlink()
        return res

    @api.multi
    def action_approve(self):
        """
        This method used for to approve the lapse leave and generate the JE and preserve the same name.
        """
        res =  super(Holidays, self).action_approve()
        for holiday in self:
            if not holiday.double_validation and holiday.holiday_status_id.accruals and holiday.lapse_leave_id and holiday.type == 'remove':
                holiday.lapse_leave_id.create_lapse_move(holiday)
        return res

    @api.multi
    def action_validate(self):
        """
        This method used for to Validate the lapse leave and generate the JE and preserve the same name.
        """
        res =  super(Holidays, self).action_validate()
        for holiday in self:
            if holiday.double_validation and holiday.holiday_status_id.accruals and holiday.lapse_leave_id and holiday.type == 'remove':
                holiday.lapse_leave_id.create_lapse_move(holiday)
        return res


class EmployeeGrade(models.Model):
    _name = "employee.grade"
    _description = "Employee Grade"

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)

    _sql_constraints = [
        ('code_uniq', 'unique (code)', "Code already exists !"),
    ]


class AutomaticLeaveAllocation(models.Model):
    _name = "automatic.leave.allocation"
    _description = "Automatic Leave Allocation"
    _rec_name = 'holiday_status_id'
    _inherit = ['mail.thread']

    holiday_status_id = fields.Many2one("hr.holidays.status",
                                        string="Leave Type", copy=False,
                                        track_visibility='onchange')
    grade_id = fields.Many2one('employee.grade', string='Grade', copy=False,
                               track_visibility='onchange')
    type = fields.Selection([
        ('prorata', 'Pro Rata'),
        ('full', 'Full'),
    ], string='Type', track_visibility='onchange', copy=False,
        default='full')
    last_alloc_date = fields.Date('Last Allocation Date',
                                  track_visibility='onchange')
    automatic_alloc_leave_line_ids = \
        fields.One2many('automatic.leave.allocation.line',
                        'automatic_leave_id', string='Leave allocated line')
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)
    department_ids = fields.Many2many('hr.department',
                                       'leave_alloc_dept_rel', 'alloc_id',
                                       'department_id')
    employee_ids = fields.Many2many('hr.employee',
                                     'leave_alloc_emp_rel', 'allocation_id',
                                     'employee_id')

    @api.onchange('company_id', 'department_ids')
    def onchange_company(self):
        """
        to set employee based on company id and department 
        :return:
        """
        domain_emp = []
        domain_dept = []
        if self.company_id:
            domain_dept.append(('company_id', '=', self.company_id.id))
            domain_emp.append(('company_id', '=', self.company_id.id))
        if self.department_ids:
            domain_emp.append(('department_id', 'in', self.department_ids.ids))
        return {'domain': {
            'employee_ids': domain_emp, 'department_ids': domain_dept}}

    @api.constrains('automatic_alloc_leave_line_ids', 'holiday_status_id')
    def check_overlaping_experience(self):
        """
        constrains fired when same type of employee status have from exp
        or to exp in between any config line
        """
        for over_line in self.automatic_alloc_leave_line_ids:
            lines = self.env['automatic.leave.allocation.line'].search(
                [('employee_status', '=', over_line.employee_status),
                 ('id', '!=', over_line.id)])
            for line in lines:
                if line.automatic_leave_id.holiday_status_id.id == \
                        over_line.automatic_leave_id.holiday_status_id.id:
                    if (over_line.from_experience > line.from_experience and
                        over_line.from_experience < line.to_experience) or \
                            (over_line.to_experience > line.from_experience
                             and over_line.to_experience < line.to_experience):
                        raise ValidationError(
                            _("Experience is Overlaping for %s Status") % 
                            dict(line._fields['employee_status'].selection).
                            get(line.employee_status))

    @api.model
    def allocate_full_leaves_automatic(self):
        """
        this method will call yearly for allocating yearly leaves
        """
        full_alloc_config = self.search([('type', '=', 'full')])
        employee_obj = self.env['hr.employee']
        holiday_obj = self.env['hr.holidays']
        date = datetime.now()
        # Start date and end date of current year.
        start_date = date.replace(day=1, month=1).date()
        end_date = date.replace(day=31, month=12).date()
        for full_alloc in full_alloc_config:
            emp_recs = False

            if full_alloc.employee_ids:
                emp_recs = full_alloc.employee_ids
                # self.env['hr.employee'].search([])
            elif full_alloc.department_ids:
                emp_recs = self.env['hr.employee'].search(
                    [('department_id', 'in', full_alloc.department_ids.ids)])
            else:
                emp_recs = self.env['hr.employee'].search(
                    [('company_id', '=', full_alloc.company_id.id)])
            if not emp_recs:
                pass
            for line in full_alloc.automatic_alloc_leave_line_ids:
                domain = [('status', '=', line.employee_status)]
                if line.from_experience and line.to_experience:
                    domain += [
                        ('current_experience', '>', line.from_experience),
                        ('current_experience', '<=', line.to_experience)]
                elif line.from_experience and not line.to_experience:
                    domain += [
                        ('current_experience', '>=', line.from_experience)]
                elif line.to_experience and not line.from_experience:
                    domain += [
                        ('current_experience', '<=', line.to_experience)]
                employees = emp_recs.search(domain)
                empployee_recs = list(set(emp_recs).intersection(employees))
                for employee_rec in empployee_recs:
                    leave_vals = {
                        'name': 'Automatic full leave allocated',
                        'state': 'confirm',
                        'type': 'add',
                        'holiday_status_id':
                            full_alloc.holiday_status_id.id,
                        'employee_id': employee_rec.id,
                        'number_of_days_temp': line.days_to_allocate,
                        'department_id':
                            employee_rec.department_id.id or False,
                        'date_from': str(start_date),
                        'date_to': str(end_date),
                    }
                    type_domain = [
                        ('date_from', '<=', end_date),
                        ('date_to', '>=', start_date),
                        ('employee_id', '=', employee_rec.id),
                        ('id', '!=', full_alloc.holiday_status_id.id),
                        ('type', '=', 'add'),
                        ('state', 'not in', ['cancel', 'refuse']),
                    ]
                    nholidays = self.env['hr.holidays'].search_count(type_domain)
                    if not nholidays:
                        leave = holiday_obj.create(leave_vals)
                        leave.action_approve()
                        if leave.holiday_status_id.double_validation:
                            leave.action_validate()
            full_alloc.last_alloc_date = str(datetime.now().date())

        self.carry_forward_leave()

        return True

    @api.model
    def carry_forward_leave(self):
        """
        this method will called when yearly scheduler called for
        creating carry forward leaves
        :return:
        """
        dtd = datetime.now()
        prev_year_date_from = dtd + relativedelta(day=1, month=1,
                                                  year=dtd.year - 1)
        prev_year_date_to = dtd + relativedelta(day=31, month=12,
                                                year=dtd.year - 1)
        holiday_status_ids = self.env['hr.holidays.status'].search([
            ('carryforward', '=', True)])
        holidays_obj = self.env['hr.holidays']
        for type in holiday_status_ids:
            employees = self.env['hr.employee'].search([])
            for emp in employees:
                domain_holidays = [('employee_id', '=', emp.id),
                                   ('holiday_status_id', '=', type.id),
                                   ('state', '=', 'validate'),
                                   ('date_from', '>=',
                                    prev_year_date_from.date()),
                                   ('date_to', '<=',
                                    prev_year_date_to.date()),
                                   ('carry_forwarded', '=',
                                    False),
                                   ]
                all_leave_recs = holidays_obj.search(domain_holidays)
                # for alloc in allocation_holiday_ids:
                taken_leave_days = sum(
                    leave.number_of_days_temp for leave in all_leave_recs
                    if leave.type == 'remove' or False)
                allocated_leave_days = sum(
                    allocate.number_of_days_temp for allocate in
                    all_leave_recs if allocate.type == 'add' or False)
                carry_froward_leave_days = \
                    min(type.no_of_days, allocated_leave_days - 
                        taken_leave_days)
                lapse_leaves = \
                    allocated_leave_days - taken_leave_days - \
                    carry_froward_leave_days
                date = datetime.now()
                allo_date_from = date + relativedelta(day=1, month=1)
                allo_date_to = allo_date_from.date().replace(
                    day=calendar.monthrange(allo_date_from.year, type.validity_months)[1],
                    month=type.validity_months)
                leave_vals = {
                    'name': 'Carry Forward Leave allocated for year '
                            '%s' % prev_year_date_from.year,
                    'state': 'confirm',
                    'type': 'add',
                    'holiday_status_id': type.id,
                    'employee_id': emp.id,
                    'number_of_days_temp': carry_froward_leave_days,
                    'carry_forwarded': True,
                    'department_id': emp.department_id.id or False,
                    'date_from': str(allo_date_from),
                    'date_to': str(allo_date_to),
                }
                if lapse_leaves > 0:
                    if type.lapse_leaves:
                        self.with_context({'lapse_remaining': True}). \
                            lapse_remaining_leave(emp, lapse_leaves, type,
                                              False)
                if carry_froward_leave_days > 0:
                    new_holiday_rec = holidays_obj.create(leave_vals)
                    new_holiday_rec.action_approve()
                    if new_holiday_rec.holiday_status_id.double_validation:
                        new_holiday_rec.action_validate()

    @api.model
    def expiry_carry_forwarded_leave(self):
        dtd = datetime.now()
        prev_year_date_from = dtd + relativedelta(day=1, month=1,
                                                  year=dtd.year)
        prev_year_date_to = dtd + relativedelta(day=31, month=12,
                                                year=dtd.year)

        carry_forwarded_holiday_ids = self.env['hr.holidays'].search([
            ('carry_forwarded', '=', True), ('type', '=', 'add'),
            ('date_from', '>=', prev_year_date_from.date()),
            ('date_to', '<=', prev_year_date_to.date())])
        for forward in carry_forwarded_holiday_ids:
            if datetime.strptime(forward.date_to, '%Y-%m-%d').date() == \
                    datetime.now().date():
                taken_leaves = self.env['hr.holidays'].search([
                    ('employee_id', '=', forward.employee_id.id),
                    ('type', '=', 'remove'),
                    ('holiday_status_id', '=', forward.holiday_status_id.id),
                    ('state', '=', 'validate'),
                    ('date_from', '>=', forward.date_from),
                    ('date_to', '<=', forward.date_to)])
                taken_leave_days = sum(leave.number_of_days_temp for leave in
                                       taken_leaves)
                if taken_leave_days < forward.number_of_days_temp:
                    lapse = forward.number_of_days_temp - taken_leave_days
                    self.with_context({'lapse_carryforwarded': True}). \
                        lapse_remaining_leave(forward.employee_id, lapse,
                                              forward.holiday_status_id, True)

    @api.model
    def lapse_remaining_leave(self, employee_id, lapse_leaves, type,
                              carry=False):
        """
        this method will called when yearly scheduler called for creating
        lapse  rempaining leave
        :return:
        """
        holidays_obj = self.env['hr.holidays']
        name = 'Lapse Leave Created'
        if carry:
            name = 'Carry Forwarded Leaves Lapse'
        leave_vals = {
            'name': name,
            'state': 'confirm',
            'type': 'remove',
            'holiday_status_id': type.id,
            'employee_id': employee_id.id,
            'number_of_days_temp': lapse_leaves,
            'department_id':
                employee_id.department_id.id or False,
            'date_from': '',
            'date_to': '',
        }
        new_holiday_rec = holidays_obj.create(leave_vals)
        ctx = dict(self._context)
        ctx.update({'lapse_leave': True})
        if ctx.get('lapse_remaining'):
            new_holiday_rec.lapse_leave = True
        if ctx.get('lapse_carryforwarded'):
            new_holiday_rec.carry_forward_lapse_leave = True
        new_holiday_rec.with_context(ctx).action_approve()
        if new_holiday_rec.holiday_status_id.double_validation:
            new_holiday_rec.with_context(ctx).action_validate()

    @api.model
    def allocate_pro_rata_leaves_automatic(self):
        """
        this method will call monthly for allocating monthly leaves
        """
        lst = []
        domain = [('type', '=', 'prorata'), ('holiday_status_id.accruals', '=', True)]
        if self.env.context.get('company_id'):
            domain.append(('company_id', '=', self.env.context.get('company_id')))
        prorata_alloc_config = self.search(domain)
        employee_obj = self.env['hr.employee']
        leave_allo_except_emp = self.env['leave.allocation.exception.emp']
        if self.env.context.get('start_date') and self.env.context.get('end_date'):
            start_date = self.env.context.get('start_date')
            end_date = self.env.context.get('end_date')
        else:
            date = datetime.now() + relativedelta(months=-1)
            # Start date and end date of current month.
            start_date = date.replace(day=1).date()
            end_date = date.replace(day=calendar.monthrange(date.year,
                                                            date.month)[1]).date()

        date = datetime.now() + relativedelta(months=-1)
        for pro_alloc in prorata_alloc_config:
            leave_obj = self.env['hr.holidays']
            if not pro_alloc.company_id == \
                    pro_alloc.holiday_status_id.company_id:
                continue
            parent_domain = []
            if pro_alloc.department_ids:
                parent_domain += [('department_id', 'in', pro_alloc.department_ids.ids)]
            if pro_alloc.employee_ids:
                parent_domain += [('id', 'in', pro_alloc.employee_ids.ids)]
            else:
                parent_domain += [('company_id', '=', pro_alloc.company_id.id)]

            for line in pro_alloc.automatic_alloc_leave_line_ids.filtered(
                    lambda x: x.days_to_allocate > 0):
                domain = [('status', '=', line.employee_status)]
                if line.from_experience and line.to_experience:
                    domain += [
                        ('current_experience', '>', line.from_experience),
                        ('current_experience', '<=', line.to_experience)]
                elif line.from_experience and not line.to_experience:
                    domain += [
                        ('current_experience', '>=', line.from_experience)]
                elif line.to_experience and not line.from_experience:
                    domain += [
                        ('current_experience', '<=', line.to_experience),
                        ('company_id', '=', pro_alloc.company_id.id)]

                final_domain = parent_domain + domain
#                 employees = employee_obj.search(domain)
                employees = employee_obj.search(final_domain)
                for employee_rec in employees.filtered(lambda l:l.contract_id and l.contract_id.is_cal_salary_accrual):
                    """Here allocation was made on employees working days.
                    as change request made by SBK project the allocation is made 
                    directly as per configuration days."""
                    # leaves_taken = leave_obj.search([
                    #                         ('employee_id', '=', employee_rec.id),
                    #                         ('state', '=', 'validate'),
                    #                         ('type', '=', 'remove'),
                    #                         ('date_from', '>=', start_date),
                    #                         ('date_to', '<=', end_date)])
                    # total_lv_tkn = sum(leave.number_of_days_temp for leave in leaves_taken)
                    # month_days = ((end_date-start_date).days) + 1
                    # worked_days = month_days - total_lv_tkn
                    # if not worked_days == 0:
                    #     allocation_day = worked_days * line.days_to_allocate / month_days
                    leave_vals = {
                        'name': 'Automatic pro-rata leave allocated',
                        'state': 'confirm',
                        'type': 'add',
                        'holiday_status_id':
                            pro_alloc.holiday_status_id.id,
                        'employee_id': employee_rec.id,
                        'number_of_days_temp': line.days_to_allocate,
                        'department_id':
                            employee_rec.department_id.id or False,
                        'date_from': str(start_date),
                        'date_to': str(end_date),
                        'company_id': employee_rec.company_id.id,
                        'is_pro_rata_leave': True,
                    }
                    # to check if any record is overlapping the same date
                    #  or not
                    existing_rec = leave_obj.search([
                        ('holiday_status_id', '=', pro_alloc.holiday_status_id.id),
                        ('date_from', '<=', start_date),
                        ('date_to', '>=', end_date),
                        ('employee_id', '=', employee_rec.id),
                        ('type', '=', 'add')
                    ])
                    if not existing_rec:
                        leave_obj += leave_obj.create(leave_vals)
                    else:
                        exception_found = leave_allo_except_emp.search(
                            [('employee_id', '=', employee_rec.id),
                             ('start_date', '=', str(start_date))])
                        if not exception_found:
                            emp_expt_val = {
                                'employee_id': employee_rec.id,
                                'company_id': pro_alloc.company_id.id,
                                'type': pro_alloc.type,
                                'holiday_status_id': pro_alloc.holiday_status_id.id,
                                'description': "You can not have 2 leaves that overlaps on same day!",
                                'start_date': str(start_date),
                                'end_date': str(end_date),
                            }
                            leave_allo_except_emp.create(emp_expt_val)

            pro_alloc.last_alloc_date = end_date
            self.create_leave_allocation_batch(pro_alloc, leave_obj)
        return True

    @api.model
    def last_month_allocate_pro_rata_leaves_automatic(self, company_lst=None, lst=None):
        if not company_lst:
            company_lst = self.env['res.company'].search([]).ids
        for company in company_lst:
#             lst = [-4, -3,-2]
            month_lst = []
            for month in lst:
                date = (datetime.now() + relativedelta(months=month)).month
                month_lst.append(date)

            for month in month_lst:
#                 date = datetime.now().date()
                date = (datetime.now().date() - relativedelta(months=month, days=1))
    #             start_date = ((datetime.now() + relativedelta(months = -1)).replace(day=1))
                start_date = datetime(year=date.year, month=month, day=1)
                end_date = (start_date + relativedelta(months=1, days=-1)).date()
                start_date = start_date.date()
                self.with_context({'start_date':start_date, 'end_date':end_date, 'company_id':company}).allocate_pro_rata_leaves_automatic()

        return True

    def create_leave_allocation_batch(self, pro_rata_config, holiday_ids):
        if holiday_ids:
            leave_allocation_obj = self.env['leave.allocation.batch']
            leave_allocation_obj = leave_allocation_obj.search([('company_id', '=', pro_rata_config.company_id.id),
                                         ('holiday_status_id', '=', pro_rata_config.holiday_status_id.id),
                                         ('date', '=', pro_rata_config.last_alloc_date),
                                         ('status', '=', 'draft')])
            leave_allocation_obj.holiday_batch_ids.unlink()
            if not leave_allocation_obj:
                leave_allocation_obj = leave_allocation_obj.create({'company_id':pro_rata_config.company_id.id,
                                       'holiday_status_id':pro_rata_config.holiday_status_id.id,
                                       'date':pro_rata_config.last_alloc_date})

            batch_lst = []
            for holiday in holiday_ids:
                leave_accrual_amount = self.get_leave_accrual_amount(holiday, holiday.employee_id)
                holiday.write({'leave_amount': leave_accrual_amount, 'batch_id':leave_allocation_obj.id})
            leave_allocation_obj.do_confirm()

    def get_leave_accrual_amount(self, holiday_id, employee_id):
        salary_wages = 0.00
        contract = employee_id.contract_id
        if contract.leave_salary_based == 'basic_salary':
            salary_wages = contract.wage
        elif contract.leave_salary_based == 'gross_salary':
            salary_wages = contract.gross_salary
        elif contract.leave_salary_based == 'basic_accommodation':
            salary_wages = contract.basic_accommodation

        leave_salary = holiday_id.get_leave_salary(datetime.strptime(holiday_id.date_from, '%Y-%m-%d'),
                        datetime.strptime(holiday_id.date_to, '%Y-%m-%d'),
                        salary_wages, holiday_id.number_of_days_temp)
        return round(leave_salary,2)

    @api.model
    def approve_pro_rata_leaves_automatic(self):
        """
        All the leave's that are create via pro rata will be in confirm state.
        here all those leave will be validated(approved).
        :return:
        """
        holidays = self.env['hr.holidays'].\
                    search([('type', '=', 'add'),
                            ('is_pro_rata_leave', '=', True),
                            ('state', '=', 'confirm')], limit=50)
        for holiday in holidays:
            holiday.action_approve()
            if holiday.double_validation:
                holiday.action_validate()
            holiday.is_pro_rata_leave = False


class AutomaticLeaveAllocationLine(models.Model):
    _name = "automatic.leave.allocation.line"
    _description = "Automatic Leave Allocation Line"

    employee_status = fields.Selection([('joined', 'Joined'),
                                        ('training', 'Training'),
                                        ('ex-training', 'Extended Training'),
                                        ('probation', 'Probation'),
                                        ('ex-probation', 'Extended Probation'),
                                        ('employment', 'Employment'),
                                        ('pip', 'PIP'),
                                        ('notice_period', 'Notice Period'),
                                        ('relieved', 'Relieved'),
                                        ('terminated', 'Terminated'),
                                        ('rejoined', 'Rejoined'),
                                        ('resign', 'Resign')],
                                       'Employee Status', default='joined')
    from_experience = fields.Float(string='From Experience')
    to_experience = fields.Float(string='To Experience')
    automatic_leave_id = fields.Many2one('automatic.leave.allocation')
    days_to_allocate = fields.Float('Days to allocate')
    company_id = fields.Many2one(related='automatic_leave_id.company_id',
                                 string='Company', store=True, readonly=True)

    @api.constrains('from_experience', 'to_experience')
    def check_to_experience(self):
        for rec in self:
            if rec.from_experience and rec.to_experience:
                if rec.to_experience < rec.from_experience:
                    raise ValidationError(
                        _("To Experience can not be less than From "
                          "Experience"))


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    current_experience = fields.Float("Current Company's Experience(Years)",
                                      compute='_compute_current_exp',
                                      search='_experience_search')

    @api.model
    def _experience_search(self, operator, operand):
        if (operator == '>' or operator == '<=' or operator == '>=') and \
                operand:
            emps = self.env['hr.employee']
            if operator == '>':
                for e in self.search([]):
                    if e.current_experience > operand:
                        emps |= e
            elif operator == '<=':
                for e in self.search([]):
                    if e.current_experience <= operand:
                        emps |= e
            elif operator == '>=':
                for e in self.search([]):
                    if e.current_experience >= operand:
                        emps |= e
            return [('id', 'in', emps.ids)]
        else:
            return [('id', 'in', [])]

    @api.multi
    def write(self, values):
        """
        this method is override for creating lapse leaves if
        employee is go to notice period
        :param values:
        :return: True
        """
        holidays_obj = self.env['hr.holidays']
        for rec in self:
            if rec.company_id.lapse_leaves:
                if 'status' in values and values.get(
                        'status') == 'notice_period':
                    allocated_leaves = holidays_obj.search([
                        ('employee_id', '=', rec.id),
                        ('type', '=', 'add')])
                    for leave in allocated_leaves:
                        name = 'Lapse Leave Created'
                        leave_vals = {
                            'name': name,
                            'state': 'confirm',
                            'type': 'remove',
                            'holiday_status_id': leave.holiday_status_id.id,
                            'employee_id': rec.id,
                            'number_of_days_temp': leave.number_of_days_temp,
                            'department_id':
                                rec.department_id.id or False,
                            'date_from': '',
                            'date_to': '',
                        }
                        new_holiday_rec = holidays_obj.create(leave_vals)
                        ctx = dict(self._context)
                        ctx.update({'lapse_leave': True})
                        new_holiday_rec.with_context(ctx).action_approve()
        return super(HrEmployee, self).write(values)


class LeaveAllowcationExceptionEmployee(models.Model):
    _name = 'leave.allocation.exception.emp'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', string='Employee')
    company_id = fields.Many2one('res.company', string='Company')
    type = fields.Char(string='Type')
    holiday_status_id = fields.Many2one('hr.holidays.status', string='Leave '
                                                                     'Type')
    description = fields.Char(string='Description')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')


class HrHolidayStatus(models.Model):
    _inherit = 'hr.holidays.status'

    carryforward = fields.Boolean(string='Carry Forward')
    no_of_days = fields.Float(string='No of Leaves')
    validity_months = fields.Integer(string='Validity(Months)')
    encashment = fields.Boolean("Encashment")
    no_of_days_encash = fields.Float(string='Leaves to Encash')
    maximum_leave_balance = fields.Float(string='Maximum Leave Balance')
    lapse_leaves = fields.Boolean(string='Lapse Leave?')
    code = fields.Char(string="Code")

    @api.constrains('validity_months')
    def check_validity_month(self):
        """
        check whether validity of carry forwarded leave is not greater than 12 months.
        :return:
        """
        for rec in self:
            if rec.validity_months > 12:
                raise ValidationError("Validity to carry forward leave must be less than or equal to 12 months")


class LapseLeaves(models.Model):
    _name = 'lapse.employee.leave'
    _rec_name = 'employee_id'
    _description = 'Lapse Leaves'

    @api.one
    @api.depends('employee_id', 'lapse_type', 'leave_type_id')
    def _compute_days(self):
        """
        this method computed total available leaves for user
        based on employee select and type to lapse
        ex: if selected lapse all it will compute all leave type
        allocated leaves else particular leave type leave
        :return:
        """
        if self.employee_id and self.lapse_type and \
                self.lapse_type == 'lapse_all':
            # Compute for all leave types
            allocated_leaves_recs = \
                self.env['hr.holidays'].search([
                    ('employee_id', '=', self.employee_id.id),
                    ('type', '=', 'add'),
                    ('state', '=', 'validate')])
            taken_leaves_recs = \
                self.env['hr.holidays'].search([
                    ('employee_id', '=', self.employee_id.id),
                    ('type', '=', 'remove'),
                    ('state', '=', 'validate')])
            allocated_days = \
                sum(leave.number_of_days_temp for leave in
                    allocated_leaves_recs)
            taken_days = \
                sum(
                    leave.number_of_days_temp for leave in taken_leaves_recs)
            self.count = allocated_days - taken_days
        if self.employee_id and self.leave_type_id and self.lapse_type and \
                self.lapse_type == 'leave_selected':
            # compute for partucal leave type
            allocated_leaves = \
                self.env['hr.holidays'].search([
                    ('employee_id', '=', self.employee_id.id),
                    ('holiday_status_id', '=', self.leave_type_id.id),
                    ('type', '=', 'add'),
                    ('state', '=', 'validate')])
            taken_leaves = \
                self.env['hr.holidays'].search([
                    ('employee_id', '=', self.employee_id.id),
                    ('holiday_status_id', '=', self.leave_type_id.id),
                    ('type', '=', 'remove'),
                    ('state', '=', 'validate')])
            allocated_days = \
                sum(leave.number_of_days_temp for leave in
                    allocated_leaves)
            taken_days = \
                sum(leave.number_of_days_temp for leave in
                    taken_leaves)
            self.count = allocated_days - taken_days

    employee_id = fields.Many2one('hr.employee', string="Employee")
    all_lapse = fields.Boolean(string="Lapse All Leaves")
    leave_type_id = fields.Many2one('hr.holidays.status', string="Leave Type")
    count = fields.Float(string="Total", compute='_compute_days')
    leaves_to_lapse = fields.Float(string="Leaves to Lapse")
    lapse_type = fields.Selection([
        ('lapse_all', 'Lapse All'),
        ('leave_selected', 'Particular Leave Type')], default="leave_selected")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)

    @api.multi
    def lapse_leaves(self):
        """
        This method is used to create lapse leaves for selected user
        :return:
        """
        holiday_obj = self.env['hr.holidays']
        if self.lapse_type and self.lapse_type == 'lapse_all':
            # For Lapse All Leaves for all leave types
            allocated_dict = {}
            taken_dict = {}
            final_dict = {}
            if self.employee_id:
                allocated_leaves = \
                    self.env['hr.holidays'].search([
                        ('employee_id', '=', self.employee_id.id),
                        ('type', '=', 'add'),
                        ('state', '=', 'validate')])
                taken_leaves = \
                    self.env['hr.holidays'].search([
                        ('employee_id', '=', self.employee_id.id),
                        ('type', '=', 'remove'),
                        ('state', '=', 'validate')])
                for alloc in allocated_leaves:
                    if alloc.holiday_status_id.id not in allocated_dict.keys():
                        allocated_dict.update(
                            {
                                alloc.holiday_status_id.id:
                                    alloc.number_of_days_temp})
                    else:
                        days = \
                            allocated_dict.get(alloc.holiday_status_id.id) + \
                            alloc.number_of_days_temp
                        allocated_dict[alloc.holiday_status_id.id] = days
                for taken in taken_leaves:
                    if taken.holiday_status_id.id not in taken_dict.keys():
                        taken_dict.update(
                            {
                                taken.holiday_status_id.id:
                                    taken.number_of_days_temp})
                    else:
                        days = \
                            taken_dict.get(taken.holiday_status_id.id) + \
                            taken.number_of_days_temp
                        taken_dict[alloc.holiday_status_id.id] = days
                for key, value in allocated_dict.items():
                    if taken_dict:
                        if key in taken_dict.keys():
                            final_dict.update(
                                {key: value - taken_dict.get(key)})
                        else:
                            final_dict.update({key: value})
                    else:
                        final_dict.update({key: value})
                
                ctx = dict(self._context)
                ctx.update({'lapse_leave': True})
                for key, value in final_dict.items():
                    if not value:
                        continue
                    hr_holiday_rec = holiday_obj.with_context(ctx).create({
                        'name': 'Lapse Leave Created',
                        'employee_id': self.employee_id.id,
                        'holiday_status_id': key,
                        'type': 'remove',
                        'number_of_days_temp': value,
                        'date_from': datetime.now().date(),
                        'date_to': datetime.now().date(),
                        'lapse_leave_id':self.id,
                        'lapse_leave': True})
                    
                    hr_holiday_rec.with_context(ctx).action_approve()
                    if hr_holiday_rec.with_context(ctx).holiday_status_id.double_validation:
                        hr_holiday_rec.with_context(ctx).action_validate()

                    ''' create JE for lapse leave '''
                    if hr_holiday_rec.holiday_status_id.accruals:
                        leave_lapse_amount = self.get_lapse_leave_request_amount()
                        if leave_lapse_amount:
                            hr_holiday_rec.leave_amount = -leave_lapse_amount
                            self.create_lapse_move(hr_holiday_rec)
        else:
            # For Lapse Leaves for particular leave type selected
            if self.employee_id and self.leave_type_id:
                allocated_leaves = \
                    self.env['hr.holidays'].search([
                        ('employee_id', '=', self.employee_id.id),
                        ('holiday_status_id', '=', self.leave_type_id.id),
                        ('type', '=', 'add'),
                        ('state', '=', 'validate')])
                taken_leaves = \
                    self.env['hr.holidays'].search([
                        ('employee_id', '=', self.employee_id.id),
                        ('holiday_status_id', '=', self.leave_type_id.id),
                        ('type', '=', 'remove'),
                        ('state', '=', 'validate')])
                allocated_days = \
                    sum(leave.number_of_days_temp for leave in
                        allocated_leaves)
                taken_days = \
                    sum(leave.number_of_days_temp for leave in
                        taken_leaves)
                remaining = allocated_days - taken_days
                if self.leaves_to_lapse > remaining:
                    raise ValidationError\
                        (_('You can not lapse leave more than '
                           'available leaves  for Leave type %s ' % 
                           self.leave_type_id.name))
                if self.leaves_to_lapse <= 0:
                    raise ValidationError (_('Please enter proper leaves to lapse day.'))
                ctx = dict(self._context)
                ctx.update({'lapse_leave': True})
                hr_holiday_rec = holiday_obj.with_context(ctx).create({
                    'name': 'Lapse Leave Created',
                    'employee_id': self.employee_id.id,
                    'holiday_status_id': self.leave_type_id.id,
                    'type': 'remove',
                    'date_from': datetime.now().date(),
                    'date_to': datetime.now().date(),
                    'number_of_days_temp': self.leaves_to_lapse,
                    'lapse_leave_id':self.id,
                    'lapse_leave': True})
                
                hr_holiday_rec.with_context(ctx).action_approve()
                if hr_holiday_rec.with_context(ctx).holiday_status_id.double_validation:
                    hr_holiday_rec.with_context(ctx).action_validate()

                ''' create JE for lapse leave '''
                if hr_holiday_rec.holiday_status_id.accruals:
                    leave_lapse_amount = self.get_lapse_leave_request_amount()
                    if leave_lapse_amount:
                        hr_holiday_rec.leave_amount = -leave_lapse_amount
                        self.create_lapse_move(hr_holiday_rec)

    def create_lapse_move(self,hr_holiday_rec):
        """
        creates journal entry while lapse the leave from the Lapse Leaves Wizard.
        create Journal Entry exactly reverse than accrual entry.
        """
        contract_id = hr_holiday_rec.employee_id.contract_id
        if not contract_id:
            raise ValidationError(_('Contract is not in running state for employee %s.' % (hr_holiday_rec.employee_id.display_name)))

        if not hr_holiday_rec.holiday_status_id.leave_salary_journal_id:
            raise ValidationError(_('Please Configured Leave Salary Journal for %s type.' % (hr_holiday_rec.holiday_status_id.name)))

        if not hr_holiday_rec.holiday_status_id.leave_salary_journal_id.default_credit_account_id:
            raise ValidationError(_('Please configured credit/debit account for %s journal.' % (hr_holiday_rec.holiday_status_id.leave_salary_journal_id.name)))

        if not hr_holiday_rec.holiday_status_id.expense_account_id:
            raise ValidationError(_('Please configured expense account for %s type.' % (hr_holiday_rec.holiday_status_id.name)))

        credit_vals = {
            'name': 'Lapse Leave',
            'credit': abs(hr_holiday_rec.leave_amount),
            'analytic_account_id':contract_id.analytic_account_id.id,
            'account_id': hr_holiday_rec.holiday_status_id.expense_account_id.id,
        }
        debit_vals = {
            'debit': abs(hr_holiday_rec.leave_amount),
            'name': 'Lapse Leave',
            'account_id': hr_holiday_rec.holiday_status_id.leave_salary_journal_id.default_credit_account_id.id,
        }
        vals = {
            'journal_id': hr_holiday_rec.holiday_status_id.leave_salary_journal_id.id,
            'date': datetime.now().date(),
            'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)],
            'ref': 'Leave Salary Accrual',
            'company_id':self.company_id.id,
            'name':hr_holiday_rec.move_name if hr_holiday_rec.move_name else '/'
        }
        move = self.env['account.move'].sudo().create(vals)
        move.post()
        move.button_cancel()
        hr_holiday_rec.write({'account_move_id' : move.id, 'move_name':move.name})


    def get_lapse_leave_request_amount(self):
        contract = self.employee_id.contract_id
        if not contract:
            raise ValidationError("Contract is not running.")
        if contract and not contract.is_cal_salary_accrual:
            return

        if contract.leave_salary_based == 'basic_salary':
            salary_wages = contract.wage
        elif contract.leave_salary_based == 'gross_salary':
            salary_wages = contract.gross_salary
        elif contract.leave_salary_based == 'basic_accommodation':
            salary_wages = contract.basic_accommodation
        else:
            raise ValidationError("Please Select Leave Salary Based On.")

        date = datetime.now().date().strftime('%Y-%m-%d')
        date = datetime.strptime(date, '%Y-%m-%d')
        month_days = calendar.monthrange(date.year, date.month)[1] or 30
        amount = ((salary_wages / month_days) * self.leaves_to_lapse)
        return amount