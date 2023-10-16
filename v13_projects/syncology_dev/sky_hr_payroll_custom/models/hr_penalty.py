# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#    Copyright (C) 2020 Skyscend Business Solutions Pvt. Ltd.(http://www.skyscendbs.com)
#
##############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PenaltyType(models.Model):
    _name = 'hr.penalty.type'
    _description = 'Penalty Types'
    _rec_name = 'name'

    name = fields.Char('Name')
    code = fields.Char('Code')
    penalty_entries = fields.One2many('hr.penalty.entries', 'penalty_type_id', 'Penalty Entries')
    rate = fields.Float('Rate')

    @api.constrains('rate')
    def _check_penalty_type_rate(self):
        if self.rate < 1:
            raise UserError(_('Rate should be greater than or equal to 1!'))


class Penalty(models.Model):
    _name = 'hr.penalty'
    _description = 'Penalties'
    _rec_name = 'reason'

    @api.depends('employee_id.first_name_arabic', 'employee_id.middle_name_arabic', 'employee_id.last_name_arabic', 'employee_id.fourth_name_arabic')
    def _compute_employee_name_arabic(self):
        for penalty in self:
            penalty.employee_arabic_name = str(penalty.employee_id.first_name_arabic) + " " + str(penalty.employee_id.middle_name_arabic) + " " + str(penalty.employee_id.last_name_arabic) + " " + str(penalty.employee_id.fourth_name_arabic)

    employee_id = fields.Many2one('hr.employee', 'Employee', ondelete='restrict', tracking=True, store=True)
    employee_arabic_name = fields.Char('Name (Arabic)', compute="_compute_employee_name_arabic", tracking=True, store=True)
    penalty_type_id = fields.Many2one('hr.penalty.type', 'Penalty Type')
    value_type = fields.Selection([('pay_cut', 'Pay Cut'), ('hours','Hours'), ('days', 'Days'), ('minutes', 'Minutes')], 'Value Type')
    value = fields.Float('Value')
    value_amount = fields.Float(related="value", string='Value')
    issued_by = fields.Many2one('res.users', string='Issued By', default=lambda self: self.env.user.id)
    reason = fields.Char('Reason')
    date = fields.Date('Date', default=fields.Date.today())
    state = fields.Selection([('pending', 'Pending'),
                              ('approved', 'Approved'),
                              ('rejected', 'Rejected')], 'State', default='pending')
    employee_salary_id = fields.Many2one('hr.employee.salary', 'Employee Salary')
    tracking_line_id = fields.Many2one('time.tracking.line', 'Tracking Line')
    amount = fields.Float('Penalty Amount')
    lock = fields.Boolean('Lock')
    parent_id = fields.Many2one('hr.employee', 'parent', related='employee_id.parent_id', store=True)
    department_id = fields.Many2one('hr.department', string='Department', related='employee_id.department_id',
                                    store=True)
    job_id = fields.Many2one('hr.job', string='Job', related='employee_id.job_id', store=True)

    @api.onchange('value_amount')
    def onchange_value_amount(self):
        """
        This method will set the value field
        ------------------------------------
        @param self: object pointer
        """
        self.value = self.value_amount

    @api.onchange('value', 'value_type', 'employee_id', 'date', 'value_amount')
    def onchange_value_type(self):
        """
        This method will update the penalty amount
        ------------------------------------------
        @param self: object pointer
        :return:
        """
        for pen in self:
            # Get actual working hours from department business hours because working schedules change sometimes
            worked_hours = 0.0
            if pen.sudo().employee_id.department_id:
                worked_hours = pen.sudo().employee_id.department_id.business_hours

            # Get working hours from working schedule as a fallback    
            if not worked_hours or worked_hours == 0.0:
                worked_hours = pen.employee_id.count_working_hours(employee_id=pen.employee_id, date=pen.date)

            if not worked_hours or worked_hours == 0.0:
                worked_hours = 1

            emp_hourly_rate = pen.sudo().employee_id.hourly_rate or 1
            
            if pen.value_type == 'pay_cut':
                pen.amount = pen.value
            else:
                pen.amount = pen.employee_id.penalty_rate * emp_hourly_rate
                # If penalty rate is not zero that it should be counted as well.
                if pen.penalty_type_id.rate != 0.0:
                    pen.amount *= pen.penalty_type_id.rate

                if pen.value_type == 'hours':
                    pen.amount *= pen.value
                elif pen.value_type == 'days':
                    pen.amount *= pen.value * worked_hours
                elif pen.value_type == 'minutes':
                    pen.amount *= pen.value / 60

    def penalty_pending(self):
        for penalty in self:
            if penalty.lock == True:
                raise UserError(_("You can not reset approved Penalties!"))
            penalty.state = 'pending'

    def penalty_approved(self):
        for penalty in self:
            penalty.state = 'approved'

    def penalty_rejected(self):
        for penalty in self:
            penalty.state = 'rejected'

    def unlink(self):
        """
        Overridden the unlink method to restrict deletion of approved penalties
        -----------------------------------------------------------------------
        @param self: object pointer
        :return True
        """
        for penalty in self:
            if penalty.lock == True:
                raise UserError(_("You can not delete approved Penalties!"))
        return super(Penalty, self).unlink()

    @api.model_create_multi
    def create(self, vals_lst):
        """
        Overridden create method to set the penalty in time tracking line
        ------------------------------------------------------------------
        :param vals_lst: A list of dictionary containing fields and values
        :return: A newly created recordset.
        """
        tracking_line_obj = self.env['time.tracking.line']
        for vals in vals_lst:
            tracking_line = tracking_line_obj.sudo().search([('employee_id', '=', vals.get('employee_id')),
                                                             ('date', '=', vals.get('date'))], limit=1)
            vals.update({'tracking_line_id': tracking_line.id})

        return super(Penalty, self).create(vals_lst)


class PenaltyEntries(models.Model):
    _name = 'hr.penalty.entries'
    _description = 'Penalty Entries'
    _rec_name = 'penalty_type_id'

    penalty_type_id = fields.Many2one('hr.penalty.type', 'Penalty Type')
    actual_time = fields.Float('Actual Time')
    actual_time_unit = fields.Selection([('minutes', 'Minutes'), ('hours','Hours'), ('days', 'Days')], 'Actual Time Unit')
    calculated_time = fields.Float('Calculated Time')
    calculated_time_unit = fields.Selection([('minutes', 'Minutes'), ('hours', 'Hours'), ('days', 'Days')],
                                        'Calculated Time Unit')
