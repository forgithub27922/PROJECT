# -*- encoding: utf-8 -*-
#
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
#

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    @api.multi
    def action_set_to_draft(self):
        res = super(HrPayslip, self).action_set_to_draft()
        for rec in self:
            rec.leave_salary_ids.write({'state':'approve'})
            rec.leave_salary_ids.mapped('leave_salary_line_ids').write({'state':'confirm','payslip_id':False})
            rec.leave_salary_ids.mapped('leave_salary_line_ids').mapped('leave_request_id').write({'leave_salary_paid':False})
        return res

    def calculate_leave_salary_amount(self):
        for rec in self:
            if rec.employee_id and rec.date_from and rec.date_to:
                leave_salary_obj = self.env['leave.salary']
                leave_salary_ids = leave_salary_obj.search([('state', '=', 'approve'), ('employee_id', '=', rec.employee_id.id), ('leave_salary_payment_mode', '=', 'salary'),
                                                            ('date', '>=', rec.date_from), ('date', '<=', rec.date_to)])

                leave_salary_ids.write({'payslip_id':rec.id})
                rec.leave_salary_amount = sum(leave_salary_ids.mapped('amount_taken'))

    leave_salary_amount = fields.Float(string='Leave Salary Amount', store=True)
    leave_request_ids = fields.One2many('leave.salary.line', 'payslip_id', string="Leave Requests")
    leave_salary_ids = fields.One2many('leave.salary', 'payslip_id', string='Leave Salaries')

    @api.multi
    def compute_sheet(self):
        if self._context.get('from_payslip'):
            return
        for payslip in self:
            payslip.calculate_leave_salary_amount()
        return super(HrPayslip, self).compute_sheet()

    @api.multi
    def action_payslip_done(self):
        """ Mark Leave Request and Leave Salary Line as paid"""
        for rec in self:
            for leave_request in rec.leave_salary_ids:
                for line in leave_request.leave_salary_line_ids:
                    line.write({'payslip_id':rec.id, 'state':'paid'})
                    line.leave_request_id.leave_salary_paid = True

                leave_request.write({'state':'paid'})

        return super(HrPayslip, self).action_payslip_done()
    
    def get_holidays(self):
        """
        search holidays for the selected employee
        :return: allocated leaves to the employee.
        and taken leave that are approved.
        """
        leave_types = self.env['hr.holidays.status'].search([('accruals', '=', True)]).ids
        domain = [
            ('employee_id', '=', self.employee_id.id or False),
            ('state', '=', 'validate'),
            ('company_id', '=', self.company_id.id or False),
            ('holiday_status_id', 'in', leave_types)]
        holidays_add = self.env['hr.holidays'].search(domain + [
            ('type', '=', 'add'),
            ('account_move_id', '!=', False)], order='date_from')
        holidays_removed = self.env['hr.holidays'].search(domain + [
            ('type', '=', 'remove'), ('leave_salary_paid', '=', True)], order='date_from')
        return holidays_add, holidays_removed

    def do_leave_salary_confirm(self):
        self.leave_salary_ids.write({'state':'paid','payslip_id':self.id})
        self.leave_salary_ids.mapped('leave_salary_line_ids').write({'state':'paid','payslip_id':self.id})
        self.leave_salary_ids.mapped('leave_salary_line_ids').mapped('leave_request_id').write({'leave_salary_paid':False})


class hr_payslip_run(models.Model):
    _inherit = 'hr.payslip.run'

    @api.multi
    def confirm_payslip(self):
        res = super(hr_payslip_run, self).confirm_payslip()
        for payslip in self.slip_ids:
            payslip.do_leave_salary_confirm()
        return res

