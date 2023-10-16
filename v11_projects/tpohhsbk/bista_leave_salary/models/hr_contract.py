# -*- encoding: utf-8 -*-
#
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
#

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class Contract(models.Model):
    _inherit = 'hr.contract'

    gross_salary = fields.Monetary('Gross Salary', digits=(16, 2), track_visibility='onchange')
    basic_accommodation = fields.Monetary('Basic + Selected Allowances', digits=(16, 2), track_visibility='onchange')
    leave_salary_based = fields.Selection(
        [('basic_salary', 'Basic Salary'), ('gross_salary', 'Gross Salary'),
         ('basic_accommodation', 'Basic + Selected Allowances')],
        string='Leave Salary Based On', default='basic_salary', track_visibility='onchange')
    date_start = fields.Date('Start Date', required=True, default=fields.Date.today,
                             help="Start date of the contract.", copy=False)
    date_end = fields.Date('End Date', copy=False,
                           help="End date of the contract (if it's a fixed-term contract).")

    old_salary_amount = fields.Float(string="Old Salary Amount")
    is_cal_salary_accrual = fields.Boolean(string="Calculate Leave Accrual", default=True, track_visibility='onchange')
    is_cal_gratuity_accrual = fields.Boolean(string="Calculate Gratuity Accrual", default=True, track_visibility='onchange')
    is_increment_paid = fields.Boolean(string="Increment Paid",copy=False)

    @api.model
    def create(self, vals):
        res = super(Contract, self).create(vals)
        amount = 0.00
        amount = res.check_old_contract_salary()
        if not amount:
            wage_dict = {'basic_salary':'wage','gross_salary':'gross_salary',
                    'basic_accommodation':'basic_accommodation'}
            contract_type = wage_dict[res.leave_salary_based]
            amount = res[contract_type]
        if amount:
            res.old_salary_amount = amount
        return res

    def check_old_contract_salary(self):
        contract_id = self.env['hr.contract'].search([('employee_id','=',self.employee_id.id),
            ('state','=','close')],limit=1,order='id desc')
        amount = 0.00
        if contract_id and not self.leave_salary_based:
            raise ValidationError('Please select Leave Salary Based On in contract!')
        if not contract_id or contract_id and not contract_id.leave_salary_based:
            return amount

        wage_dict = {'basic_salary':'wage','gross_salary':'gross_salary',
                    'basic_accommodation':'basic_accommodation'}

        contract_type = wage_dict[self.leave_salary_based]
        amount = contract_id[contract_type]
        return amount

    @api.multi
    def write(self, vals):
        if not self._context.get('from_contract') and vals.get('leave_salary_based') or vals.get('wage'):
            amount = 0.00
            wage_dict = {'basic_salary':'wage','gross_salary':'gross_salary',
                    'basic_accommodation':'basic_accommodation'}

            contract_type = wage_dict[self.leave_salary_based]
            amount = self[contract_type]
            if amount:
                vals.update({'old_salary_amount':amount,'is_increment_paid':False})
        return super(Contract, self).write(vals)

    def compute_salary(self):
        """
        Computes the gross salary and basic accommodation based on
        salary structure.
        :return:
        """
        if not self.id:
            return True
        if not self.employee_id.id:
            raise ValidationError('Please Select Employee.')
        gross_sal = 0.0
        basic_accom = 0.0
        ctx = self._context.copy()
        if self.struct_id:
            payslip_record = self.env['hr.payslip'].create({
                'employee_id': self.employee_id.id or False,
                'date_from': fields.date.today(),
                'date_to': fields.date.today(),
                'contract_id': self.id or False,
                'struct_id': self.struct_id.id or False,
            })
            payslip_record.compute_sheet()
            for line in payslip_record.line_ids:
                if line.salary_rule_id.code == 'GROSS':
                    gross_sal = line.total
                    break
            basic_accom = self.wage + \
                          sum(line.total for line in
                              payslip_record.line_ids
                              if line.salary_rule_id.is_hra)
            ctx.update({'from_contract':True})
            self.with_context(ctx).write({'gross_salary': gross_sal,
                        'basic_accommodation': basic_accom})
            if payslip_record:
                payslip_record.unlink()

    @api.constrains('state')
    def check_state(self):
        if self.state == 'open':
            is_running = self.search_count([('employee_id', '=', self.employee_id.id), ('id', '!=', self.id),
                                            ('state', '=', 'open')])
            if is_running:
                raise ValidationError('Can not set more than one contract on running state.!')

    @api.constrains('date_start', 'date_end')
    def check_overlapping(self):
        for each in self:
            domain = [('employee_id', '=', each.employee_id.id), ('state', 'in', ('draft', 'open', 'pending')), ('id', '!=', each.id),
                      '|', '|', '&', ('date_start', '<=', each.date_start), ('date_end', '>=', each.date_start),
                      '&', ('date_start', '<=', each.date_end), ('date_end', '>=', each.date_end),
                      '&', ('date_start', '<=', each.date_start), ('date_end', '=', False),
                      ]
            
            if not each.date_end:
                domain = [('employee_id', '=', each.employee_id.id), ('state', 'in', ('draft', 'open', 'pending')), ('id', '!=', each.id),
                          '|', '|', '&', ('date_start', '<=', each.date_start), ('date_end', '>=', each.date_start),
                          '&', ('date_start', '<=', each.date_start), ('date_end', '=', False),
                          ('date_start', '>=', each.date_start)]

            contract_num = self.search_count(domain)
            if contract_num:
                raise ValidationError(_('You can not have 2 contract that '
                                        'overlaps on same date!'))

                
class Employee(models.Model):

    _inherit = "hr.employee"
    
    def _compute_contract_id(self):
        """ set running contract instead of lastest contract """
        Contract = self.env['hr.contract']
        for employee in self:
            employee.contract_id = Contract.search([('employee_id', '=', employee.id), ('state', '=', 'open')], limit=1)
            
