# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError

class HrExpense(models.Model):
    _inherit = 'hr.expense'

    product_id = fields.Many2one('product.product', string='Product',readonly=False,
                                 domain=[('can_be_expensed', '=', True)], required=True)
    name = fields.Char(string='Expense Description', readonly=False, required=True)
    date = fields.Date(readonly=False, default=fields.Date.context_today, string="Expense Date")
    product_id = fields.Many2one('product.product', string='Product', readonly=False,
                                 domain=[('can_be_expensed', '=', True)], required=True)
    product_uom_id = fields.Many2one('product.uom', string='Unit of Measure', required=True, readonly=False,
                                     default=lambda self: self.env['product.uom'].search([], limit=1, order='id'))
    unit_amount = fields.Float(string='Unit Price', readonly=False, required=True,
                               digits=dp.get_precision('Product Price'))
    quantity = fields.Float(required=True, readonly=False,
                            digits=dp.get_precision('Product Unit of Measure'), default=1)
    company_id = fields.Many2one('res.company', string='Company', readonly=False,
                                 default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=False,
                                  default=lambda self: self.env.user.company_id.currency_id)
    expense_sheet_state = fields.Selection(related='sheet_id.state', string="Sheet State", store=True)

    ##Overwrite Defaults method to update state accordingly.
    @api.depends('sheet_id', 'sheet_id.account_move_id', 'sheet_id.state')
    def _compute_state(self):
        for expense in self:
            if not expense.sheet_id:
                expense.state = "draft"
            elif expense.sheet_id.state in ['submit','approve'] and not expense.is_refused:
                expense.state = "reported"
            elif expense.sheet_id.state == "cancel":
                expense.state = "refused"
            elif expense.sheet_id.state == 'draft':
                expense.state = "draft"
            elif expense.is_refused:
                expense.state = "refused"
            else:
                expense.state = "done"

    ##to update state on expense when it gets refused
    @api.multi
    def refuse_line_expense(self):
        for rec in self:
            rec.write({'is_refused':True,'state':'refused'})

    ##to update state back from refused to submit when it gets refused
    @api.multi
    def validate_refuse_line_expense(self):
        for rec in self:
            if rec.sheet_id.state == 'submit':
                rec.write({'is_refused': False, 'state': 'reported'})
            else:
                rec.write({'is_refused':False,'state':'draft'})

    ##to create journal entries according to expense
    @api.multi
    def action_move_create(self):
        records = self.filtered(lambda mv:not mv.is_refused)
        if records:
            super(HrExpense, records).action_move_create()
        else:
            return True

class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    @api.depends('expense_line_ids.unit_amount','expense_line_ids.state','expense_line_ids.is_refused')
    def _calculate_total_expense(self):
        """
        Compute the total expense.
        """
        for expense in self:
            total_expense_amount = expense_to_reimburse_amount = 0.0
            for expense_line in expense.expense_line_ids:
                total_expense_amount += expense_line.unit_amount
                if not expense_line.is_refused:
                    expense_to_reimburse_amount += expense_line.unit_amount
            expense.total_expense = expense.currency_id.round(total_expense_amount)
            expense.expense_to_reimburse = expense.currency_id.round(expense_to_reimburse_amount)



    state = fields.Selection([('draft', 'To Submit'),
                              ('submit', 'Submitted'),
                              ('approve', 'Approved'),
                              ('post', 'Posted'),
                              ('done', 'Paid'),
                              ('cancel', 'Refused')
                              ], string='Status', index=True, readonly=True,track_visibility='onchange',copy=False,
                             default='draft', required=True,
                             help='Expense Report State')
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, readonly=True,
                                  states={'draft': [('readonly', False)]},
                                  default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)],
                                                                                      limit=1))
    total_expense = fields.Monetary(string='Total Expense', store=True, readonly=True,
                                    compute='_calculate_total_expense', track_visibility='always')
    expense_to_reimburse = fields.Monetary(string='Expense To Reimburse', store=True, readonly=True,
                                           compute='_calculate_total_expense', track_visibility='always')

    ##overwrite defaults method to display amount on register payment wizard
    @api.one
    @api.depends('expense_line_ids', 'expense_line_ids.total_amount',
                 'expense_line_ids.currency_id','expense_line_ids.state',
                 'expense_line_ids.is_refused')
    def _compute_amount(self):
        total_amount = 0.0
        for expense in self.expense_line_ids:
            if not expense.is_refused:
                total_amount += expense.currency_id.with_context(
                    date=expense.date,
                    company_id=expense.company_id.id
                ).compute(expense.total_amount, self.currency_id)
            self.total_amount = total_amount

    ##submit expenses to manager
    @api.multi
    def submit_expenses(self):
        if len(self.mapped('employee_id')) != 1:
            raise UserError(_("You cannot report expenses for different employees in the same report!"))
        self.state= 'submit'
