# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime


class leave_allocation_batch(models.Model):
    _name = 'leave.allocation.batch'
    _inherit = ['mail.thread']

    name = fields.Char(string="Name")
    company_id = fields.Many2one('res.company', string="Company",default=lambda self:self.env.user.company_id.id)
    holiday_status_id = fields.Many2one('hr.holidays.status', string="Leave Type", track_visibility='onchange')
    date = fields.Date(string="Date")
    status = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'),
                               ('cancel', 'Cancel')], string="Status", default='draft',
                               track_visibility='onchange')
    move_id = fields.Many2one('account.move', string="Move")
    holiday_batch_ids = fields.One2many('hr.holidays', 'batch_id', string="Holidays Batch line ")
    move_name = fields.Char(string="Move Name", copy=False)

    @api.multi
    def unlink(self):
        for batch in self:
            if batch.holiday_batch_ids:
                if all(holiday.state != 'draft' for holiday in batch.holiday_batch_ids):
                    raise ValidationError(_("You can't delete Batch Leave Allocation!"))
                batch.holiday_batch_ids.unlink()
        return super(leave_allocation_batch, self).unlink()

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('leave.allocation.batch')
        return super(leave_allocation_batch, self).create(vals)

    @api.multi
    def do_confirm(self):
        for holiday_id in self.holiday_batch_ids:
            if holiday_id.state == 'draft':
                holiday_id.with_context({'from_batch':True}).action_confirm()
            if holiday_id.state == 'confirm':
                holiday_id.with_context({'from_batch':True}).action_approve()
                if holiday_id.double_validation:
                    holiday_id.with_context({'from_batch':True}).action_validate()

        self.create_batch_account_move()
        self.status = 'confirm'

    @api.multi
    def do_cancel(self):
        move_id = self.move_id.sudo()
        if move_id.state == 'posted':
            raise ValidationError(_("You can't cancel Leave Allocation Batch because Journal Entry already posted.!"))

        for holiday_id in self.holiday_batch_ids.filtered(lambda l:l.state != 'refuse' and l.id != self._context.get('holiday_id')):
            holiday_id.write({'leave_amount':0, 'is_batch_warning':True, 'leave_accrual_amount':0.00})
            if holiday_id.state in ['confirm', 'validate', 'validate1']:
                holiday_id.with_context({'from_batch':True}).action_refuse()

        if move_id:
            move_id.button_cancel()
            move_id.with_context({'custom_move':True}).unlink()
        self.status = 'cancel'

    @api.multi
    def do_reset_to_draft(self):
        for holiday_id in self.holiday_batch_ids:
            contract = holiday_id.employee_id.contract_id
            if contract and contract.is_cal_salary_accrual:
                # if contract.is_increment_paid:
                #     contract.is_increment_paid = False
                if not contract.leave_salary_based:
                    raise ValidationError(_('Enployee %s Contract has not configured Leave Salary Based on Type.!') % (holiday_id.employee_id.name))
                
                wage_dict = {'basic_salary':'wage','gross_salary':'gross_salary',
                    'basic_accommodation':'basic_accommodation'}
                leave_salary_type = wage_dict[contract.leave_salary_based]
                salary_wages = contract[leave_salary_type]
                leave_salary = holiday_id.get_leave_salary(datetime.strptime(holiday_id.date_from, '%Y-%m-%d'),
                        datetime.strptime(holiday_id.date_to, '%Y-%m-%d'),
                        salary_wages, holiday_id.number_of_days_temp)

                holiday_id.write({'leave_amount':leave_salary})
            if holiday_id.state == 'refuse':
                holiday_id.with_context({'from_batch':True}).action_draft()
                holiday_id.is_batch_warning = False
        self.status = 'draft'

    @api.multi
    def do_compute_leave_amount(self):
        for holiday_id in self.holiday_batch_ids:
            contract = holiday_id.employee_id.contract_id
            if contract and contract.is_cal_salary_accrual:
                # if contract.is_increment_paid:
                #     contract.is_increment_paid = False
                wage_dict = {'basic_salary':'wage','gross_salary':'gross_salary',
                    'basic_accommodation':'basic_accommodation'}
                if not contract.leave_salary_based:
                    raise ValidationError(_('Enployee %s Contract has not configured Leave Salary Based on Type.!') % (holiday_id.employee_id.name))
                leave_salary_type = wage_dict[contract.leave_salary_based]
                salary_wages = contract[leave_salary_type]
                leave_salary = holiday_id.get_leave_salary(datetime.strptime(holiday_id.date_from, '%Y-%m-%d'),
                        datetime.strptime(holiday_id.date_to, '%Y-%m-%d'),
                        salary_wages, holiday_id.number_of_days_temp)
                holiday_id.write({'leave_amount':leave_salary})

    @api.multi
    def create_batch_account_move(self):
        total_leave_amount = sum(self.holiday_batch_ids.mapped('leave_amount'))
        move_line_lst = []
        group_by_cost_center = {}
        cost_center_total_amount = 0
        for holiday_id in self.holiday_batch_ids:
            contract_id = holiday_id.employee_id.contract_id
            if contract_id and contract_id.analytic_account_id:
                if contract_id.analytic_account_id.id not in group_by_cost_center:
                    group_by_cost_center.update({contract_id.analytic_account_id.id:abs(holiday_id.leave_amount)})
                else:
                    group_by_cost_center[contract_id.analytic_account_id.id] += abs(holiday_id.leave_amount)
                cost_center_total_amount += holiday_id.leave_amount

        for key, value in group_by_cost_center.items():
            debit_vals = {
                    'name': 'Automatic pro-rata leave allocated',
                    'debit': value,
                    'analytic_account_id':key,
                    'account_id': self.holiday_status_id.expense_account_id.id,
                    }
            move_line_lst.append((0, 0, debit_vals))

        if (total_leave_amount - cost_center_total_amount):
            debit_vals = {
            'name': 'Automatic pro-rata leave allocated',
            'debit': abs(total_leave_amount - cost_center_total_amount),
            'account_id': self.holiday_status_id.expense_account_id.id,
            }
            move_line_lst.append((0, 0, debit_vals))

        credit_vals = {
            'name': self.name,
            'credit': abs(total_leave_amount),
            'account_id': self.holiday_status_id.leave_salary_journal_id. \
                              default_credit_account_id.id or False,
        }
        move_line_lst.append((0, 0, credit_vals))

        vals = {
            'journal_id': self.holiday_status_id.leave_salary_journal_id.id,
            'date': self.date,
            'line_ids': move_line_lst,
            'ref': 'Batch Leave Salary Accrual',
            'company_id':self.company_id.id
        }
        if self.move_name:
            vals['name'] = self.move_name
        move = self.env['account.move'].sudo().create(vals)
        move.post()
        self.move_name = move.name
        move.button_cancel()
        for holiday_id in self.holiday_batch_ids:
            holiday_id.write({'account_move_id':move.id})
        self.move_id = move.id

    @api.multi
    def get_journal_entry(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Journal Entry'),
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'res_id': self.move_id.id,
            'target': 'current',
            'domain':[('id', '=', self.move_id.id)]
        }
