# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#
##############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class AdditionType(models.Model):
    _name = 'hr.addition.type'
    _description = 'Hr Addition Type'
    _rec_name = 'name'

    name = fields.Char('Name')
    code = fields.Char('Code')
    rate = fields.Float('Rate')

    @api.constrains('rate')
    def _check_addition_rate(self):
        if self.rate < 1:
            raise UserError(_('Rate should be greater than or equal to 1!'))


class Addition(models.Model):
    _name = 'hr.addition'
    _description = 'Hr Addition'
    _rec_name = 'reason'

    @api.depends('employee_id.first_name_arabic', 'employee_id.middle_name_arabic', 'employee_id.last_name_arabic', 'employee_id.fourth_name_arabic')
    def _compute_employee_name_arabic(self):
        for addition in self:
            addition.employee_arabic_name = str(addition.employee_id.first_name_arabic) + " " + str(addition.employee_id.middle_name_arabic) + " " + str(addition.employee_id.last_name_arabic) + " " + str(addition.employee_id.fourth_name_arabic)

    employee_id = fields.Many2one('hr.employee', 'Employee', ondelete='restrict', tracking=True, store=True)
    employee_arabic_name = fields.Char('Name (Arabic)', compute="_compute_employee_name_arabic", tracking=True, store=True)
    addition_type_id = fields.Many2one('hr.addition.type', 'Addition Type')
    type_of_value = fields.Selection([('money', 'Money'),
                                      ('days', 'Days'),
                                      ('hours', 'Hours')], 'Type of value')
    value = fields.Float('Value')
    value_amount = fields.Float(related="value", string='Value')
    issued_by = fields.Many2one('res.users', 'Issued By', default=lambda self: self.env.uid)
    reason = fields.Char('Reason')
    rejection_reason = fields.Char('Rejection Reason')
    date = fields.Date('Date', default=fields.Date.today())
    state = fields.Selection([('pending', 'Pending'),
                              ('approved', 'Approved'),
                              ('rejected', 'Rejected')], 'Status', default='pending')
    employee_salary_id = fields.Many2one('hr.employee.salary', 'Employee Salary')
    tracking_line_id = fields.Many2one('time.tracking.line', 'Tracking Line')
    amount = fields.Float('Amount', compute='_cal_value_overtime')
    is_overtime = fields.Boolean('Overtime?', compute='_check_overtime')
    actual_overtime_hours = fields.Float('Actual Overtime Hours', compute='_cal_value_overtime')
    approved_overtime = fields.Float('Approved Overtime', compute='_cal_value_overtime')

    # Added a new bool field
    lock = fields.Boolean('Lock')
    parent_id = fields.Many2one('hr.employee', 'parent', related='employee_id.parent_id', store=True)
    department_id = fields.Many2one('hr.department', string='Department', related='employee_id.department_id',
                                    store=True)
    job_id = fields.Many2one('hr.job', string='Job', related='employee_id.job_id', store=True)

    @api.depends('addition_type_id', 'date', 'employee_id', 'type_of_value')
    def _check_overtime(self):
        """
        This will check the overtime type and set or reset the field to hide or display other fields
        --------------------------------------------------------------------------------------------
        @param self: object pointer
        """
        for add in self:
            add.is_overtime = add.addition_type_id == self.env.company.overtime_addtion_type_id

    @api.onchange('value_amount')
    def onchange_value_amount(self):
        self.value = self.value_amount

    @api.depends('date', 'value', 'value_amount', 'type_of_value', 'addition_type_id', 'employee_id')
    def _cal_value_overtime(self):
        """
        This method will update the addition amount, Approved Overtime and Actual Overtime Hours
        ----------------------------------------------------------------------------------------
        @param self: object pointer
        """
        tracking_line_obj = self.env['time.tracking.line']
        overtime_type = self.env.company.overtime_addtion_type_id
        for add in self:
            add.amount = 0.0
            add.approved_overtime = 0.0
            add.actual_overtime_hours = 0.0
            emp_hourly_rate = add.sudo().employee_id.hourly_rate or 1
            worked_hours = add.employee_id.count_working_hours(employee_id=add.employee_id, date=add.date)
            if worked_hours == 0.0:
                worked_hours = 1
            tracking_lines = tracking_line_obj.sudo().search([('employee_id', '=', add.employee_id.id),
                                                              ('date', '=', add.date)], limit=1)
            if overtime_type == add.addition_type_id:
                add.actual_overtime_hours = tracking_lines.overtime_hours
                add.approved_overtime = add.value if add.value < add.actual_overtime_hours else add.actual_overtime_hours
                add.amount = add.sudo().employee_id.addition_rate * add.approved_overtime \
                             * emp_hourly_rate * add.addition_type_id.rate

            else:
                if add.type_of_value == 'money':
                    add.amount = add.value

                elif add.type_of_value == 'hours':
                    add.amount = add.sudo().employee_id.addition_rate * add.value * emp_hourly_rate

                elif add.type_of_value == 'days':
                    add.amount = add.sudo().employee_id.addition_rate * add.value * worked_hours * emp_hourly_rate

    def action_pending(self):
        """
        This method will set the state of the addition to reset draft
        ----------------------------------------------------------
        @param self: object pointer
        """
        for add in self:
            if add.lock == True:
                raise UserError(_("You can not reset approved addition!"))
            add.state = 'pending'

    def action_approve(self):
        """
        This method will set the state of the addition to approved
        ----------------------------------------------------------
        @param self: object pointer
        """
        for add in self:
            add.state = 'approved'

    def action_reject(self):
        """
        This method will open pop wizard for reject
        -------------------------------------------
        @param self: object pointer
        """
        return {
            'name': _("Hr Addition Reject Form"),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'hr.addition.reject.wizard',
            'target': 'new',
        }

    @api.constrains('addition_type_id', 'type_of_value')
    def check_addition_overtime(self):
        """
        This method will not allow the employee to create addition request for overtime when type value not hours
        ---------------------------------------------------------------------------------------------------------
        @parm self: object pointer
        """
        for add in self:
            if self.env.company.overtime_addtion_type_id == add.addition_type_id and add.type_of_value != 'hours':
                raise ValidationError(_('You can create addition overtime with only type of value hour!'))

    @api.constrains('type_of_value')
    def check_user(self):
        """
        This method will check that if user is not payroll manager / payroll user
        then user can not create an addition with type money.
        ----------------------------------------------------------------------
        @parm self: object pointer
        """
        for add in self:
            if add.type_of_value == 'money':
                if not self.env.user.has_group(
                        'sky_hr_payroll_custom.group_payroll_manager') or not self.env.user.has_group(
                        'sky_hr_payroll_custom.group_payroll_user'):
                    raise ValidationError(_('You can not create addition with type money! Please contact your Manager!'))

    def unlink(self):
        """
        Overridden the unlink method to restrict deletion of approved additions
        -----------------------------------------------------------------------
        @param self: object pointer
        :return True
        """
        for addition in self:
            if addition.state != 'pending' or addition.lock == True:
                raise UserError(_("You can not delete approved addition!"))
        return super(Addition, self).unlink()

    @api.model_create_multi
    def create(self, vals_lst):
        """
        Overridden create method to set the addition in time tracking line
        ------------------------------------------------------------------
        :param vals_lst: A list of dictionary containing fields and values
        :return: A newly created recordset.
        """
        tracking_line_obj = self.env['time.tracking.line']
        for vals in vals_lst:
            tracking_line = tracking_line_obj.sudo().search([('employee_id', '=', vals.get('employee_id')),
                                                             ('date', '=', vals.get('date'))], limit=1)
            vals.update({'tracking_line_id': tracking_line.id})

        return super(Addition, self).create(vals_lst)
