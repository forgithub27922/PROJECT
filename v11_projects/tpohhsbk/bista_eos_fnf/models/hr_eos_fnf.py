# -*- encoding: utf-8 -*-
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from odoo.tools import float_round
import calendar


class HrTerminateRequest(models.Model):
    _inherit = 'hr.termination.request'

    eos_fnf_ids = fields.One2many('hr.eos.fnf', 'terminate_id',
                                  string='FNF Details')
    expense_ids = fields.Many2many('hr.expense.sheet', string="Expense")
    payslip_id = fields.Many2one('hr.payslip', string="Payslips")
    final_ff_amount = fields.Float(compute='_get_final_ff_amount' ,string="Full & Final Amount")
    loan_ids = fields.One2many('hr.employee.loan', 'termination_req_id',
                               string="Loan", copy=False)
    slip_ids = fields.One2many('hr.payslip', 'termination_req_id', string='Payslips',
                               states={'draft': [('readonly', False)]})
    salary_ids = fields.One2many('hr.salary.payable', 'termination_req_id', string='Leave Salary')
    spl_allowance_ids = fields.One2many('hr.special.allowances', 'termination_req_id', string='Special Allowances')
    other_deduct_ids = fields.One2many('hr.other.deductions', 'termination_req_id', string='Other Deductions')
    gratuity_final_pmnt_ids = fields.One2many('hr.gratuity.final.payment', 'termination_req_id', string='Gratuity Accrual')
    # allowance_expense_account_id = fields.Many2one('account.account', string='Allowance Expense Account')
    # deduction_account_id = fields.Many2one('account.account', string='Deduction Account')
    account_move_id = fields.Many2one('account.move', string='Journal Entry',
                                      copy=False)
    gtt_max_payabel = fields.Float('Max. Gratuity Payable', compute='_get_max_gratuity')

    @api.multi
    def action_view_payslip(self):
        payslip_id = self.mapped('payslip_id')
        action = self.env.ref('hr_payroll.action_view_hr_payslip_form').read()[0]
        if len(payslip_id) > 1:
            action['domain'] = [('id', 'in', payslip_id.ids)]
        elif len(payslip_id) == 1:
            action['views'] = [(self.env.ref('hr_payroll.view_hr_payslip_form').id, 'form')]
            action['res_id'] = payslip_id.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.multi
    @api.depends('gratuity_final_pmnt_ids')
    def _get_max_gratuity(self):
        """
        sets max gratuity to be paid
        :return:
        """
        for rec in self:
            total_gtt = sum(gtt.gratuity_amount for gtt in rec.gratuity_final_pmnt_ids)
            if total_gtt > (rec.employee_id.contract_id.wage * 24):
                rec.gtt_max_payabel = (rec.employee_id.contract_id.wage * 24)
            else:
                rec.gtt_max_payabel = total_gtt

    @api.multi
    def action_view_expences(self):
        expences = self.mapped('expense_ids')
        action = self.env.ref('hr_expense.action_hr_expense_sheet_my_all').read()[0]
        if len(expences) > 1:
            action['domain'] = [('id', 'in', expences.ids)]
        elif len(expences) == 1:
            action['views'] = [(self.env.ref('hr_expense.view_hr_expense_sheet_form').id, 'form')]
            action['res_id'] = expences.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.multi
    @api.depends('eos_fnf_ids', 'expense_ids',
                 'payslip_id', 'pay_off_amount', 'salary_ids',
                 'spl_allowance_ids', 'other_deduct_ids','gratuity_final_pmnt_ids')
    def _get_final_ff_amount(self):
        for data in self:
            deduction = 0
            allowance = 0
            for ff in data.eos_fnf_ids:
                if ff.is_deduction:
                    deduction += ff.amount
                else:
                    allowance += ff.amount
            deduction += data.pay_off_amount
            data.final_ff_amount = allowance - deduction

    @api.multi
    def do_reset_to_draft(self):
        self.state = 'draft'

    @api.multi
    def action_calculate_fnf(self):
        """
        :return: Calculate F&F amount for employee.
        """
        self.ensure_one()
        fnf_lst = [(6,0, {})]
        expense_sheet_obj = self.env['hr.expense.sheet']

        # For Expenses:
        expense_sheet_ids = expense_sheet_obj.search(
            [('employee_id', '=', self.employee_id.id),
             ('state', '=', 'approve')])
        self.expense_ids = expense_sheet_ids.ids

        total_expense = sum(sheet_expense.total_amount
                            for sheet_expense in expense_sheet_ids) or 0.0
        if total_expense:
            fnf_lst.append((0, 0,
                            {
                                'terminate_id': self.id,
                                'name': 'Total expense Employee (to reimburse)',
                                'amount': total_expense,
                            }))

        loan_ids = self.env['hr.employee.loan'].search([('employee_id', '=', self.employee_id.id),(
            'state', '=', 'approved'),('remaining_installments_total_amount', '>', 0)])

        loan_due = 0
        for loan in loan_ids:
            loan_due += loan.remaining_installments_total_amount
        if loan_due:
            fnf_lst.append((0, 0, self.get_eos_fnf_line('Loan Due', loan_due, True)))
        # payslip_total_payable = sum(slip.net_amount for slip in self.slip_ids)

        payslip_total_payable = 0.00
        for paylip in self.slip_ids:
            if paylip.state != 'paid':
                payslip_total_payable += paylip.net_amount
            else:
                paylip.write({'termination_req_id':False})

        if payslip_total_payable:
            fnf_lst.append((0, 0, self.get_eos_fnf_line('Salary Payable', payslip_total_payable, False)))
        self.calculate_salary_payable()
        leave_salary_payabel_total = sum(ls_line.leave_salary_amount for ls_line in self.salary_ids)
        if leave_salary_payabel_total:
            fnf_lst.append((0, 0, self.get_eos_fnf_line('Leave Salary Payable', leave_salary_payabel_total, False)))
        spl_alwnc_total = sum(alwnce_line.base_crncy_amount for alwnce_line in self.spl_allowance_ids)
        if spl_alwnc_total:
            fnf_lst.append((0, 0, self.get_eos_fnf_line('Special Allowances', spl_alwnc_total, False)))
        other_dedct_total = sum(deduction_line.base_crncy_amount for deduction_line in self.other_deduct_ids)
        if other_dedct_total:
            fnf_lst.append((0, 0, self.get_eos_fnf_line('Other Deductions', other_dedct_total, True)))
        self.calculate_final_gratuity()
        gtty_accrual_total = sum(gtty_line.gratuity_amount for gtty_line in self.gratuity_final_pmnt_ids)
        if gtty_accrual_total:
            if gtty_accrual_total > (self.employee_id.contract_id.wage * 24):
                gtty_accrual_total = (self.employee_id.contract_id.wage * 24)
            fnf_lst.append((0, 0, self.get_eos_fnf_line('Gratuity Accrual', gtty_accrual_total, False)))
        asset_penalties_total = sum(asset.penalties for asset in self.employee_asset_ids)
        if asset_penalties_total:
            fnf_lst.append((0, 0, self.get_eos_fnf_line('Assets Penalty', asset_penalties_total, True)))
        self.eos_fnf_ids = fnf_lst
        self.write({'loan_ids': [(6, 0, loan_ids.ids)]})
        return True

    def get_eos_fnf_line(self, name, amount, is_deduction):
        """
        :param name: that to be set fnf record
        :param amount: amount to be set in fnf record
        :param is_deduction: if its deduction it must me True else False
        :return: dictionary of fnf record.
        """
        return {'terminate_id': self.id,
                'name': name,
                'amount': amount,
                'is_deduction': is_deduction
                }

    @api.multi
    def generate_payslip(self):
        """
        If last month payslip is not created one confirmation box will open.
        :return: confirmation wizard
        """
        lst_month_fst_date = fields.Date.to_string(fields.Date.from_string(self.relieve_date)
                                                    + relativedelta(day=1, months=-1))
        crnt_month_fst_date = fields.Date.to_string(fields.Date.from_string(self.relieve_date)
                                                    + relativedelta(day=1))
        payslip_ids = self.env['hr.payslip'].search([('employee_id', '=', self.employee_id.id),
                                                     ('payslip_run_id','=',False),
                                                     ('state', 'in', ('draft','done'))])
        last_payslip = payslip_ids[-1:]
        if not last_payslip or last_payslip.date_from < lst_month_fst_date \
                or last_payslip.date_from < crnt_month_fst_date:
            action = self.env.ref('bista_eos_fnf.action_wiz_confirmation_payslip')
            result = {
                'name': action.name,
                'type': action.type,
                'view_type': 'form',
                'view_mode': 'form',
                'target': action.target,
                'context': self._context,
                'res_model': action.res_model,
            }
            return result

    def calculate_salary_payable(self):
        """
        calculate leave salary and salary payable amount of individual type
        for particular employee.
        :return:
        """
        self.write({'salary_ids': [(2, self.salary_ids.ids)]})
        contract = self.employee_id.contract_id
        if not contract:
            raise ValidationError("Employee %s Contract is not running.!" % (self.employee_id.name))
        leave_types = self.env['hr.holidays.status'].search([('accruals', '=', True),
        ('company_id','=',self.company_id.id)]).ids
        for rec in leave_types:
            leave_accrued = 0.0
            holiday_status_id = 0
            domain = [
                ('employee_id', '=', self.employee_id.id or False),
                ('state', '=', 'validate'),
                ('holiday_status_id', '=', rec)]
            holidays_add = self.env['hr.holidays'].search(domain + [
                ('type', '=', 'add')], order='date_from')
            holidays_removed = self.env['hr.holidays'].search(domain + [
                ('type', '=', 'remove')], order='date_from')
            for holiday in holidays_add:
                leave_accrued += holiday.number_of_days_temp
                holiday_status_id = holiday.holiday_status_id.id
            removed_days = sum(hl_removed.number_of_days_temp for hl_removed in holidays_removed if hl_removed.holiday_status_id.id == holiday_status_id)
            diff_days = leave_accrued - removed_days
            if diff_days > 0.0:
                amount = ((contract.wage * 12) / 365)
                vals = {
                        'leave_type_id': holiday_status_id or False,
                        'leave_balance': diff_days,
                        'leave_salary_amount': amount * diff_days,
                        'termination_req_id': self.id,
                }
                self.env['hr.salary.payable'].create(vals)

    def calculate_final_gratuity(self):
        """
        Calculates gratuity of particular employee according to employee experience and
        gratuity configuration. create gratuity final payment item yearly. for eos_fnf
        :return:
        """
        if not self.employee_id.date_employment:
            raise ValidationError(_('Employment Date not found for %s !') % (self.employee_id.name))
        self.write({'gratuity_final_pmnt_ids': [(2, self.gratuity_final_pmnt_ids.ids)]})
        gratuity_id = self.env['hr.gratuity'].search([('company_id', '=', self.employee_id.company_id.id)])
        experience = 0.0
        days_flag = True
        
        if self.employee_id.contract_id and not self.employee_id.contract_id.is_cal_gratuity_accrual:
            return
        if self.employee_id.contract_id and self.employee_id.date_employment:
            wages = self.employee_id.contract_id.wage
            date_relieve_from = fields.Date.from_string(self.relieve_date)
            employment_date = fields.Date.from_string(self.employee_id.date_employment)
            has_next_month = True
            list_exp_req = 0
            gtt_date = fields.Date.from_string(gratuity_id.date)
            new_date = employment_date
            while (has_next_month == True):

                end_date = (new_date + relativedelta(years=+1)) + relativedelta(days=-1)
                gratuity_line_ids = self.env['hr.gratuity']
                if new_date < gtt_date and \
                        self.employee_id.country_id.id == self.employee_id.company_id.country_id.id:
                    gratuity_line_ids = gratuity_id.nationality_ids
                elif new_date < gtt_date and \
                        self.employee_id.country_id.id != self.employee_id.company_id.country_id.id:
                    gratuity_line_ids = gratuity_id.other_nationality_ids
                elif new_date >= gtt_date and self.type == 'voluntary':
                    gratuity_line_ids = gratuity_id.resignation_contract_ids
                    if not list_exp_req:
                        list_exp_req = gratuity_line_ids.sorted(key=lambda l: l.from_experience)[0].from_experience
                        if self.employee_id.total_relevant_experience < list_exp_req:
                            break
                    exp = self.get_experience(employment_date, date_relieve_from)
                    for line in gratuity_line_ids:
                        if exp >= line.from_experience and exp < line.to_experience:
                            while (has_next_month == True):
                                if end_date <= date_relieve_from:
                                    # if days_flag:
                                    #     current_month_last_date = new_date + relativedelta(months=+1,day=1,days=-1)
                                    #     emp_experience = self.get_experience(employment_date, current_month_last_date)
                                    #     if emp_experience < list_exp_req:
                                    #         emp_experience = list_exp_req
                                    #     eligible_gratuity = self.get_gratuity(gratuity_line_ids, emp_experience)
                                    #     diff_days = (current_month_last_date - new_date).days + 1
                                    #     date_end = current_month_last_date + relativedelta(days=+1)
                                    #     print ("\n\n- -diff_days--",diff_days,eligible_gratuity,emp_experience)

                                    #     total_gtt_amount = self.cal_gratuity_line_total(wages, eligible_gratuity, new_date, date_end)
                                    #     print("\n\n --total_gtt_amount---",total_gtt_amount,eligible_gratuity.days)
                                    #     gratuity_days = float_round(((eligible_gratuity.days * diff_days+1) / 365), 2)
                                    #     print ("\n\n ---301----",gratuity_days)
                                    #     self.create_gratuity_accraul(new_date, current_month_last_date, emp_experience, gratuity_days, total_gtt_amount, self.id)
                                    #     new_date = current_month_last_date + relativedelta(days=+1)
                                    #     end_date = (new_date + relativedelta(years=+1,days=-1))
                                    #     print ("\n\n- --303---",new_date,end_date)
                                    #     days_flag = False
                                    # else:
                                    emp_experience = self.get_experience(employment_date, end_date)
                                    if emp_experience < list_exp_req:
                                        emp_experience = list_exp_req
                                    total_gtt_amount = ((self.employee_id.contract_id.wage * line.days) / 30)
                                    self.create_gratuity_accraul(new_date, end_date, emp_experience, line.days,
                                                                    total_gtt_amount, self.id)
                                    new_date = end_date + relativedelta(days=+1)
                                    end_date = (new_date + relativedelta(years=+1)) + relativedelta(days=-1)
                                elif end_date > date_relieve_from and new_date < date_relieve_from:
                                    date_end = date_relieve_from + relativedelta(days=+1)
                                    emp_experience = self.get_experience(employment_date, date_end)
                                    if emp_experience < list_exp_req:
                                        emp_experience = list_exp_req
                                    total_gtt_amount = self.cal_gratuity_line_total(wages, line, new_date, date_end)
                                    gratuity_days = float_round(((line.days * (date_end - new_date).days + 1) / 365), 2)
                                    self.create_gratuity_accraul(new_date, date_relieve_from, emp_experience,
                                                                 gratuity_days , total_gtt_amount, self.id)
                                    new_date = fields.Date.from_string(self.relieve_date) + relativedelta(days=+1)
                                    end_date = (new_date + relativedelta(years=+1)) + relativedelta(days=-1)
                                else:
                                    has_next_month = False
                        elif exp == line.from_experience and exp == line.to_experience:
                            while (has_next_month == True):
                                if end_date <= date_relieve_from:
                                    emp_experience = self.get_experience(employment_date, end_date)
                                    if emp_experience < list_exp_req:
                                        emp_experience = list_exp_req
                                    total_gtt_amount = ((self.employee_id.contract_id.wage * line.days) / 30)
                                    self.create_gratuity_accraul(new_date, end_date, emp_experience, line.days,
                                                                 total_gtt_amount, self.id)
                                    new_date = end_date + relativedelta(days=+1)
                                    end_date = (new_date + relativedelta(years=+1)) + relativedelta(days=-1)
                                elif end_date > date_relieve_from and new_date < date_relieve_from:
                                    date_end = date_relieve_from + relativedelta(days=+1)
                                    emp_experience = self.get_experience(employment_date, date_end)
                                    if emp_experience < list_exp_req:
                                        emp_experience = list_exp_req
                                    total_gtt_amount = self.cal_gratuity_line_total(wages, line,
                                                                                    new_date, date_end)
                                    gratuity_days = float_round(((line.days * (date_end - new_date).days + 1) / 365), 2)
                                    self.create_gratuity_accraul(new_date, date_relieve_from, emp_experience,
                                                                 gratuity_days, total_gtt_amount, self.id)
                                    new_date = fields.Date.from_string(self.relieve_date) + relativedelta(days=+1)
                                    end_date = (new_date + relativedelta(years=+1)) + relativedelta(days=-1)
                                else:
                                    has_next_month = False
                        elif exp > line.from_experience and not line.to_experience:
                            gratuity_line_fixed = gratuity_line_ids.filtered(lambda line:line.from_experience == line.to_experience)
                            updated_end_date = self.get_fixed_exp_date(employment_date, new_date, gratuity_line_fixed)
                            while (has_next_month):
                                if new_date < updated_end_date:
                                    if end_date > updated_end_date and new_date < updated_end_date\
                                            and updated_end_date <= date_relieve_from:
                                        emp_experience = self.get_experience(employment_date, updated_end_date)
                                        if emp_experience < list_exp_req:
                                                emp_experience = list_exp_req
                                        total_gtt_amount = self.cal_gratuity_line_total(wages, gratuity_line_fixed,
                                                                                        new_date, updated_end_date)
                                        gratuity_days = float_round(((gratuity_line_fixed.days * (updated_end_date - new_date).days + 1) / 365), 2)
                                        self.create_gratuity_accraul(new_date, updated_end_date, emp_experience,
                                                                     gratuity_days, total_gtt_amount, self.id)
                                        new_date = updated_end_date + relativedelta(days=+1)
                                        end_date = (new_date + relativedelta(years=+1)) + relativedelta(days=-1)
                                    elif end_date <= updated_end_date and end_date <= date_relieve_from:
                                        date_end = end_date + relativedelta(days=+1)
                                        emp_experience = self.get_experience(employment_date, date_end)
                                        if emp_experience < list_exp_req:
                                            emp_experience = list_exp_req
                                        total_gtt_amount = self.cal_gratuity_line_total(wages, gratuity_line_fixed,
                                                                                        new_date, date_end)
                                        self.create_gratuity_accraul(new_date, updated_end_date, emp_experience, float_round(((gratuity_line_fixed.days * (date_end - new_date).days) / 365), 2), total_gtt_amount, self.id)
                                        new_date = updated_end_date + relativedelta(days=+1)
                                        end_date = (new_date + relativedelta(years=+1)) + relativedelta(days=-1)
                                elif new_date >= updated_end_date and new_date <= date_relieve_from:
                                    if end_date <= date_relieve_from:
                                        emp_experience = self.get_experience(employment_date, end_date)
                                        if emp_experience < list_exp_req:
                                            emp_experience = list_exp_req
                                        total_gtt_amount = ((self.employee_id.contract_id.wage * line.days) / 30)
                                        self.create_gratuity_accraul(new_date, end_date, emp_experience, line.days, total_gtt_amount, self.id)
                                        new_date = end_date + relativedelta(days=+1)
                                        end_date = (new_date + relativedelta(years=+1)) + relativedelta(days=-1)
                                    elif end_date > date_relieve_from and new_date < date_relieve_from:
                                        date_end = date_relieve_from + relativedelta(days=+1)
                                        emp_experience = self.get_experience(employment_date, date_end)
                                        if emp_experience < list_exp_req:
                                            emp_experience = list_exp_req
                                        total_gtt_amount = self.cal_gratuity_line_total(wages, line,
                                                                                        new_date, date_end)
                                        gratuity_days = float_round(((line.days * (date_end - new_date).days + 1) / 365), 2)
                                        self.create_gratuity_accraul(new_date, date_relieve_from, emp_experience, gratuity_days, total_gtt_amount, self.id)
                                        new_date = fields.Date.from_string(self.relieve_date) + relativedelta(days=+1)
                                        end_date = (new_date + relativedelta(years=+1)) + relativedelta(days=-1)
                                else:
                                    has_next_month = False
                    break
                # Termination Gratuity Calculations.
                elif new_date >= gtt_date and self.type == 'forced':
                    gratuity_line_ids = gratuity_id.termination_contract_ids
                if not gratuity_line_ids:
                    break
                if not list_exp_req:
                    list_exp_req = gratuity_line_ids.sorted(key=lambda l: l.from_experience)[0].from_experience
                    if self.employee_id.total_relevant_experience < list_exp_req:
                        break
                if new_date < date_relieve_from:
                    if end_date <= date_relieve_from and \
                        end_date < gtt_date and not new_date > gtt_date:
                        emp_experience = self.get_experience(employment_date, end_date + relativedelta(days=+1))
                        if emp_experience < list_exp_req:
                            emp_experience = list_exp_req
                        eligible_gratuity = self.get_gratuity(gratuity_line_ids, emp_experience)
                        total_gtt_amount = ((self.employee_id.contract_id.wage * eligible_gratuity.days) / 30)
                        self.create_gratuity_accraul(new_date, end_date, emp_experience, eligible_gratuity.days, total_gtt_amount, self.id)
                        new_date = end_date + relativedelta(days=+1)
                    elif end_date <= date_relieve_from and \
                            new_date < gtt_date and end_date >= gtt_date:
                        emp_experience = self.get_experience(employment_date, (gtt_date + relativedelta(days=-1)))
                        if emp_experience < list_exp_req:
                            emp_experience = list_exp_req
                        eligible_gratuity = self.get_gratuity(gratuity_line_ids, emp_experience)
                        total_gtt_amount = self.cal_gratuity_line_total(wages, eligible_gratuity, new_date, gtt_date)
                        gratuity_days = float_round(((eligible_gratuity.days * (gtt_date - new_date).days) / 365), 2)
                        self.create_gratuity_accraul(new_date, gtt_date + relativedelta(days=-1), emp_experience, gratuity_days, round(total_gtt_amount), self.id)
                        new_date = gtt_date
                    
                    # New Rule Wise Termination Gratuity calculate.
                    elif end_date <= date_relieve_from and \
                            new_date >= gtt_date and end_date > gtt_date:
                        # Break the year as per the new rule Using Flag.
                        # For Ex: New Rule start from 23/03/2017 to Current Month End Date. 
                        if days_flag:
                            current_month_last_date = new_date + relativedelta(months=+1,day=1,days=-1)
                            emp_experience = self.get_experience(employment_date, current_month_last_date)
                            if emp_experience < list_exp_req:
                                emp_experience = list_exp_req
                            eligible_gratuity = self.get_gratuity(gratuity_line_ids, emp_experience)
                            diff_days = (current_month_last_date - new_date).days + 1
                            date_end = current_month_last_date + relativedelta(days=+1)

                            total_gtt_amount = self.cal_gratuity_line_total(wages, eligible_gratuity, new_date, date_end)
                            gratuity_days = float_round(((eligible_gratuity.days * diff_days+1) / 365), 2)
                            self.create_gratuity_accraul(new_date, current_month_last_date, emp_experience, gratuity_days, total_gtt_amount, self.id)
                            new_date = current_month_last_date + relativedelta(days=+1)
                            days_flag = False
                        else:
                            emp_experience = self.get_experience(employment_date, end_date + relativedelta(days=+1))
                            if emp_experience < list_exp_req:
                                emp_experience = list_exp_req
                            eligible_gratuity = self.get_gratuity(gratuity_line_ids, emp_experience)
                            date_end = end_date + relativedelta(days=+1)
                            total_gtt_amount = self.cal_gratuity_line_total(wages, eligible_gratuity, new_date, date_end)
                            gratuity_days = float_round(((eligible_gratuity.days * (date_end - new_date).days) / 365), 2)
                            self.create_gratuity_accraul(new_date, end_date, emp_experience, gratuity_days, total_gtt_amount, self.id)
                            new_date = end_date + relativedelta(days=+1)

                    elif end_date >= date_relieve_from and new_date < date_relieve_from\
                            and new_date >= gtt_date:
                        emp_experience = self.get_experience(employment_date, date_relieve_from + relativedelta(days=+1))
                        if emp_experience < list_exp_req:
                            emp_experience = list_exp_req
                        eligible_gratuity = self.get_gratuity(gratuity_line_ids, emp_experience)
                        date_end = date_relieve_from + relativedelta(days=+1)
                        total_gtt_amount = self.cal_gratuity_line_total(wages, eligible_gratuity, new_date, date_end)
                        gratuity_days = float_round(((eligible_gratuity.days * (date_end - new_date).days + 1) / 365), 2)
                        self.create_gratuity_accraul(new_date, self.relieve_date, emp_experience, gratuity_days,
                                                     round(total_gtt_amount), self.id)
                        new_date = end_date + relativedelta(days=+1)
                else:
                    has_next_month = False

    def get_gratuity(self, gratuity_line_ids, emp_experience):
        list_exp_req = gratuity_line_ids.sorted(key=lambda l: l.from_experience)[0].from_experience
        for gratuity in gratuity_line_ids:
            if emp_experience > gratuity.from_experience and \
                    emp_experience <= gratuity.to_experience:
                return gratuity
            elif emp_experience > gratuity.from_experience and \
                    gratuity.to_experience == 0.0:
                return gratuity
        if emp_experience == list_exp_req:
            return gratuity_line_ids.sorted(key=lambda l: l.from_experience)[0]

    def get_experience(self, employment_date, new_date):
        """
        Finds experience of particular employee on date specified.
        :param employment_date:
        :param new_date:
        :return:
        """
        experience = 0.0
        rd = relativedelta(new_date, employment_date)
        experience = (rd.years)
        if rd.months:
            experience += (rd.months / 12)
        if rd.days:
            experience += (rd.days / 365)
        return experience

    def get_fixed_exp_date(self, employment_date, new_date, gratuity_line):
        """
        finds end date when needs to calculate gratuity while from_experience and to_experience
        are similar(till which date needs to calculate fixed gratuity) currently used for resignation.
        :param employment_date:
        :param new_date:
        :param gratuity_line:
        :return:
        """
        end_date = False
        experience = 0.0
        if gratuity_line.from_experience == gratuity_line.to_experience:
            end_date = new_date
            experience = self.get_experience(employment_date, end_date)
            while True:
                if experience < gratuity_line.to_experience:
                    end_date = end_date + relativedelta(days=+1)
                    experience = self.get_experience(employment_date, end_date)
                else:
                    break
        return end_date

    def create_gratuity_accraul(self, start_date, end_date, experience, gratuity_days, total_gtt_amount, termination_req_id):
        """
        creates record of gratuity final payment based on provided data
        :param start_date:
        :param end_date:
        :param experience:
        :param gratuity_days:
        :param total_gtt_amount:
        :param termination_req_id:
        :return:
        """
        vals = {'start_date': start_date,
                'end_date': end_date,
                'experience': experience,
                'gratuity_days': gratuity_days,
                'gratuity_amount': round(total_gtt_amount),
                'termination_req_id': termination_req_id}
        self.env['hr.gratuity.final.payment'].create(vals)

    def cal_gratuity_line_total(self, wages, eligible_gratuity, date_start, date_end):
        """
        calculates total amount for particular gratuity line
        :param wages:
        :param eligible_gratuity:
        :param date_start:
        :param date_end:
        :return: total gratuity amount
        """
        gtt_years = relativedelta(date_end, date_start).years
        gtt_months = relativedelta(date_end, date_start).months
        gtt_days = relativedelta(date_end, date_start).days
        return round((((wages * eligible_gratuity.days) / 30) * gtt_years) +
                    ((((wages * eligible_gratuity.days) / 30) / 12) * gtt_months) +
                    ((((wages * eligible_gratuity.days) / 30) / 365) * gtt_days))

    def create_accrual_line(self, gratuity, employee, new_date, start_date):
        """
        Calculate accrual monthly of particular employee eos_fnf
        :param gratuity:
        :param employee:
        :param new_date:
        :param start_date:
        :return:
        """
        gratuity_days = 0.0
        amount = 0.0
        now = fields.Date.from_string(self.relieve_date)
        if not start_date:
            start_date = new_date
        if (new_date.year % 4) == 0:
            if new_date.year == now.year and new_date.month == now.month:
                gratuity_days = float_round(((now.day * gratuity.days) / 366), precision_rounding=0.01)
            else:
                gratuity_days = float_round((((calendar.monthrange(new_date.year, new_date.month)[1])
                                 * gratuity.days) / 366), precision_rounding=0.01)
            amount = ((employee.contract_id.wage * 12) / 366) * gratuity_days
        else:
            if new_date.year == now.year and new_date.month == now.month:
                gratuity_days = float_round(((now.day * gratuity.days) / 365), precision_rounding=0.01)
            else:
                gratuity_days = float_round((((calendar.monthrange(new_date.year,\
                                                      new_date.month)[1]) * gratuity.days) / 365), precision_rounding=0.01)
            amount = ((employee.contract_id.wage * 12) / 365) * gratuity_days
        return float_round(gratuity_days, precision_rounding=0.01), float_round(amount, precision_rounding=0.01), start_date

    @api.multi
    def action_open_journal_entries(self):
        action = self.env.ref('account.action_move_journal_line')
        result = {
            'name': action.name,
            'type': action.type,
            'view_type': 'form',
            'view_mode': 'form',
            'target': action.target,
            'context': self._context,
            'res_id': self.account_move_id.id,
            'res_model': action.res_model,
        }
        return result


class HrTerminateRequest(models.Model):
    _name = 'hr.eos.fnf'

    name = fields.Char('Description')
    amount = fields.Float('Amount')
    is_deduction = fields.Boolean(string="Is Deduction", copy=False)
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  related='company_id.currency_id',
                                  store=True)
    terminate_id = fields.Many2one('hr.termination.request', 'Terminate ID')


class EmployeeLoan(models.Model):
    _inherit = 'hr.employee.loan'

    termination_req_id = fields.Many2one('hr.termination.request', 'Termination Request')
    

class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip'

    termination_req_id = fields.Many2one('hr.termination.request', 'Termination Request')


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    is_leave_deduction = fields.Boolean('Is Leave Deduction', defaul='false')


class HrSalaryPayable(models.Model):
    _name = 'hr.salary.payable'

    leave_type_id = fields.Many2one('hr.holidays.status', 'Leave Type')
    leave_balance = fields.Float('Leave Balance')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.user.company_id.currency_id,
                                  store=True)
    leave_salary_amount = fields.Float('Leave Salary Amount')
    termination_req_id = fields.Many2one('hr.termination.request', 'Termination Request')


class HrSpecialAllowances(models.Model):
    _name = 'hr.special.allowances'
    _description = 'Hr Special Allowances'

    description = fields.Char('Description')
    currency_id = fields.Many2one('res.currency', 'Currency',  default=lambda self: self.env.user.company_id.currency_id.id)
    amount = fields.Float('Amount')
    base_crncy_amount = fields.Float('Base Currency Amount')
    termination_req_id = fields.Many2one('hr.termination.request', 'Termination Request')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    company_currency_id = fields.Many2one(string="Currency", related='company_id.currency_id', readonly=True)
    allowance_expense_account_id = fields.Many2one('account.account', string='Allowance Account')


    @api.onchange('amount', 'currency_id')
    def change_amount(self):
        for rec in self:
            total = rec.currency_id.with_context(date=fields.Date.today()).\
                compute(rec.amount,rec.company_id.currency_id)
            rec.base_crncy_amount = total


class HrOtherDeductions(models.Model):
    _name = 'hr.other.deductions'
    _description = 'Hr Other Deductions'

    description = fields.Char('Description')
    currency_id = fields.Many2one('res.currency', 'Currency',
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    amount = fields.Float('Amount')
    base_crncy_amount = fields.Float('Base Currency Amount')
    termination_req_id = fields.Many2one('hr.termination.request', 'Termination Request')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    company_currency_id = fields.Many2one(string="Currency", related='company_id.currency_id', readonly=True)
    deduction_account_id = fields.Many2one('account.account', string='Deduction Account')

    @api.onchange('amount', 'currency_id')
    def change_amount(self):
        for rec in self:
            total = rec.currency_id.with_context(date=fields.Date.today()).\
                compute(rec.amount,rec.company_id.currency_id)
            rec.base_crncy_amount = total


class HrGratuityFinalPayment(models.Model):
    _name = 'hr.gratuity.final.payment'
    _description = 'Hr Gratuity Final Payment'

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    experience = fields.Float('Experience')
    gratuity_days = fields.Float('Gratuity Days')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  default=lambda self: self.env.user.company_id.currency_id,
                                  store=True)
    gratuity_amount = fields.Float('Gratuity Amount')
    termination_req_id = fields.Many2one('hr.termination.request', 'Termination Request')