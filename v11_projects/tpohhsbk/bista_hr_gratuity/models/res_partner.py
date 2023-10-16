# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import fields, models, api
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
import calendar


class ResPartnerGratuityAccrual(models.Model):
    _name = 'res.partner.gratuity.accrual'
    _description = 'Gratuity Accrual'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', string='Employee')
    start_date = fields.Date('Start Date', compute='compute_start_date', store=True)
    end_date = fields.Date('End Date', compute='compute_end_date', store=True)
    days_accrued = fields.Float('Days Accrued', compute='compute_days_amount_accrued', store=True)
    amount_accrued = fields.Float('Amount Accrued', compute='compute_days_amount_accrued', store=True)
    state = fields.Selection([('accrual', 'Accrual'), ('paid', 'Paid')],
                             readonly=True, copy=False, default='accrual')
    accrual_line_ids = fields.One2many('gratuity.accrual.line', 'gtt_accrual_id',
                                       string='Accrual Line')
    advance_line_ids = fields.One2many('gratuity.advance.line', 'gtt_accrual_id',
                                       string='Advance Line')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.user.company_id)
    @api.one
    @api.depends('accrual_line_ids.gratuity_amount',
                  'accrual_line_ids.gratuity_days',
                 'advance_line_ids.state',
                 'advance_line_ids.advance_amount')
    def compute_days_amount_accrued(self):
        self.days_accrued = sum(line.gratuity_days for line in self.accrual_line_ids)
        accrual_total = sum(line.gratuity_amount for line in self.accrual_line_ids)
        advance_paid = sum(line.advance_amount for line in self.advance_line_ids if line.state == 'paid' )
        self.amount_accrued = (accrual_total - advance_paid)

    @api.depends('accrual_line_ids.start_date')
    def compute_start_date(self):
        if self.accrual_line_ids:
            self.start_date = self.accrual_line_ids.sorted(key=lambda l:l.start_date)[0].start_date

    @api.depends('accrual_line_ids.end_date')
    def compute_end_date(self):
        if self.state == 'paid' and self.accrual_line_ids[-1:]:
            self.start_date = self.accrual_line_ids[-1:].end_date


class GratuityAccrualLine(models.Model):
    _name = 'gratuity.accrual.line'
    _description = 'Gratuity Accrual Line'

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    gratuity_days = fields.Float('Gratuity Days')
    gratuity_amount = fields.Float('Gratuity Amount')
    gtt_accrual_id = fields.Many2one('res.partner.gratuity.accrual', 'Employee Gratuity Accrual')
    account_move_id = fields.Many2one('account.move', string="Journal Entry")

    @api.model
    def automatic_hr_gratuity_calculation(self):
        """
        Generates gratuity automatic for previous month of employees
        :return:
        """
        company_ids = self.env['res.company'].search([])
        gtt_accrual_exception_obj = self.env['gratuity.accrual.exception']
        for company in company_ids:
            if not company.gratuity_journal_id:
                desc = 'Please configure gratuity journal on company %s ' % company.name
                grt_jrn_exp_id = gtt_accrual_exception_obj.search([('company_id', '=', company.id),
                                                  ('description', '=', desc)],limit=1)
                if not grt_jrn_exp_id:
                    grty_missing_jrnl_vals = {
                        'employee_id': False,
                        'company_id': company.id,
                        'description': desc,
                        'date': fields.date.today(),
                    }
                    gtt_accrual_exception_obj.create(grty_missing_jrnl_vals)
                continue
            if not company.gratuity_account_id:
                desc = 'Please configure gratuity expense account on company %s ' % company.name
                grt_acnt_exp_id = gtt_accrual_exception_obj.search([('company_id', '=', company.id),
                                                  ('description', '=', desc)],limit=1)
                if not grt_acnt_exp_id:
                    grty_missing_exp_ac_vals = {
                        'employee_id': False,
                        'company_id': company.id,
                        'description': desc,
                        'date': fields.date.today(),
                    }
                    gtt_accrual_exception_obj.create(grty_missing_exp_ac_vals)
                continue

            gratuity_id = self.env['hr.gratuity'].search([('company_id', '=', company.id)])
            if not gratuity_id:
                desc = 'Gratuity configure missing for the company %s ' % company.name
                grt_config_exp_id = gtt_accrual_exception_obj.search([('company_id', '=', company.id),
                                                  ('description', '=', desc)],limit=1)
                if not grt_config_exp_id:
                    grty_config_exp_vals = {
                        'employee_id': False,
                        'company_id': company.id,
                        'description': desc,
                        'date': fields.date.today(),
                    }
                    gtt_accrual_exception_obj.create(grty_config_exp_vals)
                continue
            gratuity_accrual_obj = self.env['res.partner.gratuity.accrual']
            employee_ids = self.env['hr.employee'].search([('status','not in',['relieved','terminated','rejoined']),
                                                           ('company_id','=', company.id)])
            for employee in employee_ids:
                employee_desc = "Employment Date Not Found %s " % employee.display_name
                desc = "Contract does not Exist"
                gtt_acrl_exc_id = gtt_accrual_exception_obj.search([('employee_id', '=', employee.id),
                                                  ('company_id', '=', company.id),
                                                  ('description', '=', desc)],limit=1)
                
                employee_gtt_acrl_exc_id = gtt_accrual_exception_obj.search([('employee_id', '=', employee.id),
                                                  ('company_id', '=', company.id),
                                                  ('description', '=', employee_desc)],limit=1)

                if not employee.date_employment and not employee_gtt_acrl_exc_id:
                    gtt_accrual_exception_vals = {
                        'employee_id' : employee.id,
                        'company_id' : company.id,
                        'description': employee_desc,
                        'date': fields.date.today(),
                    }
                    gtt_accrual_exception_obj.create(gtt_accrual_exception_vals)
                    continue
                if not employee.contract_id and not gtt_acrl_exc_id:
                    gtt_accrual_exception_vals = {
                        'employee_id' : employee.id,
                        'company_id' : company.id,
                        'description': desc,
                        'date': fields.date.today(),
                    }
                    gtt_accrual_exception_obj.create(gtt_accrual_exception_vals)
                    continue
                elif not employee.contract_id and gtt_acrl_exc_id:
                    continue
                elif employee.contract_id and gtt_acrl_exc_id:
                    gtt_acrl_exc_id.unlink()
                for gratuity in gratuity_id.termination_contract_ids:
                    if employee.current_experience >= gratuity.from_experience and \
                        employee.current_experience < gratuity.to_experience:
                        emp_gratuity = gratuity_accrual_obj.search([('employee_id', '=', employee.id),
                                                                    ('state', '=', 'accrual'),
                                                                    ('company_id','=',company.id)])
                        if not emp_gratuity:
                            gratuity_vals = {
                                'employee_id': employee.id,
                                'state': 'accrual',
                                'company_id': company.id,
                            }
                            new_created_gratuity = gratuity_accrual_obj.create(gratuity_vals)
                            self.create_last_accrual_line(gratuity, employee, new_created_gratuity)
                        else:
                            self.create_last_accrual_line(gratuity, employee, emp_gratuity)
                    elif employee.current_experience >= gratuity.from_experience and \
                        gratuity.to_experience == 0.0:
                        emp_gratuity = gratuity_accrual_obj.search([('employee_id', '=', employee.id),
                                                                    ('state', '=', 'accrual'),
                                                                    ('company_id', '=',company.id)])
                        if not emp_gratuity:
                            gratuity_vals = {
                                'employee_id': employee.id,
                                'state': 'accrual',
                                'company_id': company.id,
                            }
                            new_created_gratuity = gratuity_accrual_obj.create(gratuity_vals)
                            self.create_last_accrual_line(gratuity, employee, new_created_gratuity)
                        else:
                            self.create_last_accrual_line(gratuity, employee, emp_gratuity)
            self._cr.commit()

    def create_last_accrual_line(self, gratuity, employee, gratuity_accrual):
        """
        calculate gratuity accrual line and makes journal entry.
        :param gratuity:
        :param employee:
        :param gratuity_accrual:
        :return:
        """
        last_month_date = fields.date.today() + relativedelta(months=-1)
        lst_month_fst_dt = last_month_date + relativedelta(day=1)
        lst_month_lst_dt = (last_month_date + relativedelta(months=1, day=1)) + relativedelta(days=-1)
        exist_accrual = self.search([('start_date', '=', lst_month_fst_dt),
                                    ('end_date', '=', lst_month_lst_dt),
                                    ('gtt_accrual_id', '=', gratuity_accrual.id)])
        
        if not exist_accrual:
            gratuity_days = 0.0
            amount = 0.0
            if (last_month_date.year % 4) == 0:
                if gratuity.allowed_gratuity_days:
                    gratuity_days = gratuity.allowed_gratuity_days

                else:
                    gratuity_days = ((calendar.monthrange(last_month_date.year, last_month_date.month)[1])
                                     * gratuity.days) / 366

                amount = ((employee.contract_id.wage * 12) / 366) * gratuity_days
            else:
                if gratuity.allowed_gratuity_days:
                    gratuity_days = gratuity.allowed_gratuity_days

                else:
                    gratuity_days = ((calendar.monthrange(last_month_date.year,
                                                      last_month_date.month)[1]) * gratuity.days) / 365
                amount = ((employee.contract_id.wage * 12) / 365) * gratuity_days

            accrual_line_vals = {
                'start_date': lst_month_fst_dt,
                'end_date': lst_month_lst_dt,
                'gratuity_days': gratuity_days,
                'gratuity_amount': amount,
                'gtt_accrual_id': gratuity_accrual.id or False,
            }
            accrual_line = self.create(accrual_line_vals)
            debit_vals = {
                'name': 'Gratuity Accrual',
                'debit': amount,
                'credit': 0.0,
                'account_id': employee.company_id.gratuity_account_id.id or False,
                'analytic_account_id':employee.contract_id.analytic_account_id.id,
                'partner_id': employee.partner_id.id or False,
            }
            credit_vals = {
                'debit': 0.0,
                'credit': amount,
                'account_id': employee.company_id.gratuity_journal_id. \
                                  default_credit_account_id.id or False,
                'partner_id': employee.partner_id.id or False,
            }
            vals = {
                'journal_id': employee.company_id.gratuity_journal_id.id,
                'date': fields.date.today(),
                'state': 'draft',
                'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)],
                'ref': 'Gratuity Accrual'
            }
            move = self.env['account.move'].create(vals)
            # move.post()
            accrual_line.write({'account_move_id': move.id})


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


class GratuityAdvanceLine(models.Model):
    _name = 'gratuity.advance.line'
    _description = 'Gratuity Advance Line'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', string='Employee')
    request_date = fields.Date('Request Date', default=fields.date.today())
    advance_amount = fields.Float('Advance Amount')
    accrued_amount = fields.Float('Accrued Amount',)
    state = fields.Selection([('requested','Requested'),
                              ('confirmed','Confirmed'),
                              ('approved','Approved'),
                              ('paid','Paid'),
                              ('rejected','Rejected')], default='requested', copy=False)
    gtt_accrual_id = fields.Many2one('res.partner.gratuity.accrual', 'Employee Gratuity Accrual')
    account_move_id = fields.Many2one('account.move', string="Journal Entry")

    @api.onchange('employee_id')
    def get_gratuity_accrual_amount(self):
        self.ensure_one()
        emp_gratuity_id = self.env['res.partner.gratuity.accrual'].search([('employee_id', '=', self.employee_id.id),
                                                         ('state', '=', 'accrual')])
        self.gtt_accrual_id = emp_gratuity_id.id
        self.accrued_amount = emp_gratuity_id.amount_accrued

    def action_confirm_advance_gratuity(self):
        self.write({'state': 'confirmed'})

    def action_approve_advance_gratuity(self):
        self.write({'state': 'approved'})

    def action_reject_request_advance_gratuity(self):
        self.write({'state': 'rejected'})

    @api.constrains('advance_amount')
    def check_advance_amount(self):
        self.ensure_one()
        if self.advance_amount > self.accrued_amount:
            raise ValidationError('Advance amount must not be greater than accrued amount')

    @api.multi
    def action_open_adv_journal_entries(self):
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


class GratuityAccrualException(models.Model):
    _name = 'gratuity.accrual.exception'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', string='Employee')
    company_id = fields.Many2one('res.company', string='Company')
    description = fields.Char(string='Description')
    date = fields.Date(string='Date')
