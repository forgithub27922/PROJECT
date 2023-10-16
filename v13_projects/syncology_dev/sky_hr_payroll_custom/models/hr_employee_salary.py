# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#
##############################################################################
from odoo import models, fields, api, _
from datetime import date
import calendar
from odoo.exceptions import UserError


class HrEmployeeSalary(models.Model):
    _name = 'hr.employee.salary'
    _description = 'Employee Salary'
    _rec_name = 'employee_id'

    @api.depends('employee_id.first_name_arabic', 'employee_id.middle_name_arabic', 'employee_id.last_name_arabic', 'employee_id.fourth_name_arabic')
    def _compute_employee_name_arabic(self):
        for salary in self:
            salary.employee_arabic_name = str(salary.employee_id.first_name_arabic) + " " + str(salary.employee_id.middle_name_arabic) + " " + str(salary.employee_id.last_name_arabic) + " " + str(salary.employee_id.fourth_name_arabic)

    employee_id = fields.Many2one('hr.employee', 'Employee')
    employee_arabic_name = fields.Char('Employee (Arabic)', compute="_compute_employee_name_arabic", tracking=True, store=True)
    basic = fields.Float('Basic')
    performance = fields.Float('Performance')
    addition_ids = fields.One2many('hr.addition', 'employee_salary_id', 'Additions')
    additions = fields.Float('Additions Amount', compute='_calc_addition', store=True)
    gross = fields.Float('Gross Salary', compute='_calc_gross', store=True)
    penalty_ids = fields.One2many('hr.penalty', 'employee_salary_id', 'Penalties')
    paycuts = fields.Float('Paycuts Amount', compute='_calc_paycut', store=True)
    net = fields.Float('Net Salary', compute='_calc_net', store=True)
    annual_bonus = fields.Float('Annual Bonus')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    state = fields.Selection([('draft', 'Draft'),
                              ('confirmed', 'Confirmed'),
                              ('approved', 'Approved')], 'Status', default='draft')
    parent_id = fields.Many2one('hr.employee', 'parent', related='employee_id.parent_id', store=True)
    department_id = fields.Many2one('hr.department', string='Department', related='employee_id.department_id',
                                    store=True)
    job_id = fields.Many2one('hr.job', string='Job', related='employee_id.job_id', store=True)

    insurance = fields.Boolean('Insurance',related='employee_id.insurance',)
    ins_cut_value = fields.Float('Insurance cut value', related='employee_id.ins_cut_value')
    fellowship_fund = fields.Boolean('Fellowship Fund', related='employee_id.fellowship_fund')
    fellowship_cut_value = fields.Float('Fellowship Fund cut value', related='employee_id.fellowship_cut_value')
    staff_children_cut = fields.Float('Staffs children cut', related='employee_id.staff_children_cut')
    other_cut = fields.Float('Other cut', related='employee_id.other_cut')
    cuts = fields.Float('Total cut', compute='_calc_total_cut')

    senior_allowance = fields.Float('Senior Allowance', related='employee_id.senior_allowance')
    transition_allowance = fields.Float('Transition Allowance', related='employee_id.transition_allowance')
    lms_allowance = fields.Float('LMS Allowance', related='employee_id.lms_allowance')
    travel_allowance_driver = fields.Float('Travel Allowance For Drivers', related='employee_id.travel_allowance_driver')
    supervision_maintenance_allowance = fields.Float('Supervision and maintenance Allowance', related='employee_id.supervision_maintenance_allowance')
    other_allowance = fields.Float('Other Allowance', related='employee_id.other_allowance')
    allowance = fields.Float('Total Allowance', compute='_calc_total_allowance')
    
    @api.depends('addition_ids')
    def _calc_addition(self):
        """
        This method will calculate the additions
        ----------------------------------------
        @param self: object pointer
        """
        for add in self:
            add.additions = sum(add.addition_ids.mapped('amount'))

    @api.depends('penalty_ids')
    def _calc_paycut(self):
        """
        This method will calculate the penalties
        ----------------------------------------
        @param self: object pointer
        """
        for penalty in self:
            penalty.paycuts = sum(penalty.penalty_ids.mapped('amount'))

    @api.depends('basic', 'additions')
    def _calc_gross(self):
        """
        This method will calculate the gross salary
        -------------------------------------------
        @param self: object pointer
        """
        for sal in self:
            sal.gross = sal.basic + sal.additions 

    @api.depends('ins_cut_value', 'fellowship_cut_value', 'staff_children_cut', 'other_cut')
    def _calc_total_cut(self):
        """
        This method will calculate the Total cuts
        -------------------------------------------
        @param self: object pointer
        """
        for sal in self:
            total_cut = 0.0
            total_cut += sal.ins_cut_value + sal.fellowship_cut_value + sal.staff_children_cut + sal.other_cut
            sal.cuts = total_cut

    @api.depends('senior_allowance', 'transition_allowance', 'lms_allowance', 'travel_allowance_driver', 'supervision_maintenance_allowance', 'other_allowance')
    def _calc_total_allowance(self):
        """
        This method will calculate the Total Allowance
        -------------------------------------------
        @param self: object pointer
        """
        for sal in self:
            total_allowance = 0.0
            total_allowance += sal.senior_allowance + sal.transition_allowance + sal.lms_allowance + sal.travel_allowance_driver + sal.supervision_maintenance_allowance + sal.other_allowance

            sal.allowance = total_allowance

    @api.depends('basic', 'additions', 'paycuts')
    def _calc_net(self):
        """
        This method will calculate net gross salary
        -------------------------------------------
        @param self: object pointer
        """
        for sal in self:
            sal.net = sal.basic + sal.additions + sal.allowance - sal.paycuts - sal.cuts

    @api.model
    def default_get(self, fields):
        """
        Overridden default_get method to set the start and end date of previous month
        -----------------------------------------------------------------------------
        @param self: object pointer
        @param fields: list of fields which are having default values
        :return: a dictionary containing fields and their default values
        """
        res = super(HrEmployeeSalary, self).default_get(fields)
        current_date = date.today()
        month = current_date.month - 1
        year = current_date.year
        if month == 0:
            month = 12
            year -= 1
        month_range = calendar.monthrange(year, month)
        start_date = date(year, month, 1)
        end_date = date(year, month, month_range[1])
        res.update({'start_date': start_date, 'end_date': end_date})
        return res

    @api.onchange('employee_id')
    def onchange_employee(self):
        """
        On Change employee method to bring the salary and bonus from employee
        ---------------------------------------------------------------------
        @param self: object pointer
        """

        for sal in self:
            salary = 0.0
            bonus = 0.0
            if sal.employee_id:
                if sal.employee_id.is_confidential== True and not self.user_has_groups('sky_hr_payroll_custom.group_payroll_manager'):
                    raise UserError("You can not see Confidential Salaries!")
                salary = sal.employee_id.salary
                bonus = sal.employee_id.annual_bonus
            sal.basic = salary
            sal.annual_bonus = bonus

    @api.onchange('start_date', 'end_date', 'employee_id')
    def onchange_dates(self):
        """
        This is an onchange method which will fetch the additions and penalties
        for the employee between the selected dates.
        -----------------------------------------------------------------------
        @param self: object pointer
        """
        addition_obj = self.env['hr.addition']
        penalty_obj = self.env['hr.penalty']
        for sal in self:
            adds = addition_obj.search([
                ('employee_id', '=', sal.employee_id.id),
                ('date', '>=', sal.start_date),
                ('date', '<=', sal.end_date),
                ('state', '=', 'approved')
            ])
            sal.addition_ids = [(6, 0, adds.ids)]
            pens = penalty_obj.search([
                ('employee_id', '=', sal.employee_id.id),
                ('date', '>=', sal.start_date),
                ('date', '<=', sal.end_date),
                ('state', '=', 'approved')
            ])
            sal.penalty_ids = [(6, 0, pens.ids)]

    def action_confirm(self):
        """
        This method will set the state of the hr employee salary to confirm
        -------------------------------------------------------------------
        @param self: object pointer
        """
        for salary in self:
            salary.state = 'confirmed'

    def action_approve(self):
        """
        This method will set the state of the hr employee salary to confirm
        -------------------------------------------------------------------
        @param self: object pointer
        """
        leave_obj = self.env['hr.leave']
        leave_rec = leave_obj.search([('employee_id', '=', self.employee_id.id), ('state', '=', 'validate')])
        time_tracking_line_obj = self.env['time.tracking.line']
        time_tracking_line_rec = time_tracking_line_obj.search([
            ('employee_id', '=', self.employee_id.id),
            ('date', '>=', self.start_date),
            ('date', '<=', self.end_date)
        ])
        for salary in self:
            for additions in salary.addition_ids:
                additions.lock = True
            for penalties in salary.penalty_ids:
                penalties.lock = True
            for leaves in leave_rec:
                leaves.lock = True
            for time_tracking_line in time_tracking_line_rec:
                time_tracking_line.lock = True
            salary.state = 'approved'

    def unlink(self):
        for salary in self:
            if salary.state != 'draft':
                raise UserError(_("You can delete data in Draft state"))
        return super(HrEmployeeSalary, self).unlink()
