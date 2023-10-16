# -*- encoding: utf-8 -*-
#
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
#
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import ValidationError, UserError


class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    travel_id = fields.Many2one('hr.travel', string="Travel Ref.")


class HrTravel(models.Model):

    _name = 'hr.travel'
    _description = 'Travel details of the employee.'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', string='Employee')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    duration = fields.Integer(compute='get_duration', string='Duration')
    country_id = fields.Many2one('res.country', string='Destination Country')
    travel_type = fields.Selection([('local', 'Local'),
                                    ('international', 'International')],
                                    string='Travel Type')
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)
    expense_ids = fields.One2many('hr.expense', 'travel_id', string='Expenses')
    allowance_ids = fields.One2many('hr.allowances.line', 'travel_id', string='Allowances')
    notes = fields.Text('Notes')
    state = fields.Selection([('draft', 'Draft'), ('scheduled', 'Scheduled'),
                              ('onsite', 'Onsite'), ('returned', 'Returned'),
                              ('completed', 'Completed'),
                              ('canceled', 'Canceled')], default='draft',
                             string='State')
    travel_ticket_ids = fields.One2many('hr.travel.ticket', 'travel_id', string="Tickets Details")
    journal_id = fields.Many2one('account.journal', string='Expense Journal', states={'done': [('readonly', True)], 'post': [('readonly', True)]},
        default=lambda self: self.env['ir.model.data'].xmlid_to_object('hr_expense.hr_expense_account_journal') or self.env['account.journal'].search([('type', '=', 'purchase')], limit=1),
        help="The journal used when the travel expense is done.")
    bank_journal_id = fields.Many2one('account.journal', string='Bank Journal', states={'done': [('readonly', True)], 'post': [('readonly', True)]}, default=lambda self: self.env['account.journal'].search([('type', 'in', ['cash', 'bank'])], limit=1), help="The payment method used when the travel expense is paid by the company.")
    account_id = fields.Many2one('account.account', string='Account')
    move_id = fields.Many2one('account.move', string="Journal Entry")
    visa_ids = fields.One2many('hr.visa', 'travel_id', string='Visa Details',
                               domain=[('type', '=', 'employee')])

    @api.model
    def default_get(self, fields_list):
        res = super(HrTravel, self).default_get(fields_list)
        emp_id = self.env['hr.employee'].browse(self._context.get('active_id'))
        res.update({'employee_id': emp_id.id})
        return res

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        visa_obj_ids = self.env['hr.visa'].search([('employee_id','=', self.employee_id.id),
                                                   ('type', '=', 'employee')])
        for visa_obj in visa_obj_ids:
            visa_obj.family_member_id = ''
            visa_obj.family_relation_id = ''
        self.visa_ids = visa_obj_ids

    @api.multi
    def post_journal_entry(self):
        if self.move_id:
            raise UserError("Account entry already created.")
        ctx = (self._context)
        journal_rec = self.journal_id or False
        partner_rec = self.employee_id.address_home_id or \
                      self.employee_id.partner_id or False
#         payment_type = self.payment_type
        if not partner_rec:
            raise ValidationError(_("Employee have no partner!"))
        partner_name = partner_rec.name

        move_lines = []
        for line in self.allowance_ids:
            #Multi currency.
            company_currency = self.company_id.currency_id
            diff_currency = line.currency_id != company_currency
            if line.currency_id != company_currency:
                amount_currency = self.currency_id.with_context(ctx).\
                    compute(line.amount, company_currency)
            else:
                amount_currency = False
                
            debit, credit, amount_currency, dummy = self.env['account.move.line']\
                .with_context(date=self.start_date).compute_amount_fields(
                line.amount, line.currency_id, line.company_id.currency_id)
    
            debit_vals = {
                'name': partner_name,
                'debit': abs(debit),
                'credit': 0.0,
                'account_id': self.account_id.id,
                'amount_currency': diff_currency and amount_currency,
                'currency_id': diff_currency and line.currency_id.id,
                'allownce_id': self.id,
                'partner_id': partner_rec.id or False,
            }
            move_lines.append((0,0,debit_vals))
            credit_vals = {
                'name': line.name,
                'debit': 0.0,
                'credit': abs(debit),
                'account_id':
                    journal_rec.default_debit_account_id
                    and journal_rec.default_debit_account_id.id or False,
                'amount_currency': diff_currency and -amount_currency,
                'currency_id': diff_currency and self.currency_id.id,
                'allownce_id': self.id,
            }
            move_lines.append((0,0,credit_vals))
        vals = {
            'journal_id': journal_rec.id,
            'date': fields.date.today(),
            'state': 'draft',
            'line_ids': move_lines,
            'ref': 'Allowances'
        }
        move = self.env['account.move'].create(vals)
        self.move_id = move.id
        move.post()
        return move
        
    @api.multi
    def btn_confirm(self):
        for rec in self:
            rec.state = 'scheduled'

    @api.multi
    def btn_onsite(self):
        for rec in self:
            rec.state = 'onsite'

    @api.multi
    def btn_return(self):
        for rec in self:
            rec.state = 'returned'

    @api.multi
    def btn_complate(self):
        for rec in self:
            rec.state = 'completed'

    @api.multi
    def btn_cancel(self):
        for rec in self:
            rec.state = 'canceled'

    @api.depends('start_date', 'end_date')
    def get_duration(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                st_dt = datetime.strptime(
                    rec.start_date, "%Y-%m-%d").date()
                ed_dt = datetime.strptime(
                    rec.end_date, "%Y-%m-%d").date()
                diff = ed_dt - st_dt
                rec.duration = diff.days + 1

    @api.multi
    @api.constrains('start_date', 'end_date', 'employee_id')
    def _check_dates(self):
        for record in self:
            if record.start_date and record.end_date:
                if record.start_date > record.end_date:
                    raise ValidationError(
                        _('End Date must be greater than Start Date!'))
                if record.employee_id:
                    old_travel_recs = record.search([
                        ('employee_id', '=', record.employee_id.id),
                        ('id', '!=', record.id)])
                    for old_travel_rec in old_travel_recs:
                        if old_travel_rec.start_date and \
                                old_travel_rec.end_date:
                            if old_travel_rec.start_date <= \
                                    record.start_date <= \
                                    old_travel_rec.end_date:
                                raise ValidationError(
                                    "You cannot overlap travel dates for same "
                                    "employee!")
                            if old_travel_rec.start_date <= \
                                    record.end_date <= \
                                    old_travel_rec.end_date:
                                raise ValidationError(
                                    "You cannot overlap travel dates for same "
                                    "employee!")

    @api.multi
    def calc_allowances(self):
        context = dict(self._context)
        context.update({'country_id': self.country_id.id})
        return {
            'name': ("Allowances"),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'wiz.allowances',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'context': context,
            'target': 'new',

        }

    @api.model
    def create(self, vals):
        res = super(HrTravel, self).create(vals)
        if res.expense_ids:
            vals = {'name': res.employee_id.name + ' Expense' + '(' + res.start_date + ' To ' + res.end_date + ')',
                    'employee_id': res.employee_id.id,
                    'payment_mode': 'own_account',
                    'travel_id':res.id}
            hr_expense_sheet_id = self.env['hr.expense.sheet'].create(vals)
            for expense in res.expense_ids:
                hr_expense_sheet_id.with_context({'from_create': True}).write({'expense_line_ids': [(4, expense.id)]})
        return res

    @api.multi
    def write(self, vals):
        res = super(HrTravel, self).write(vals)
        if vals.get('expense_ids', []):
            hr_expense_sheet_obj = self.env['hr.expense.sheet']
            for travel in self:
                hr_expense_sheet_id = hr_expense_sheet_obj.search([('travel_id', '=', travel.id),
                                                                   ('state', '=', 'draft')])
                if hr_expense_sheet_id:
                    for expense in travel.expense_ids:
                        hr_expense_sheet_id.write({'expense_line_ids': [(4, expense.id)]})
        return res


class HrTravelTicket(models.Model):
    _name = 'hr.travel.ticket'

    name = fields.Char('Description')
    source = fields.Char('Source')
    destination = fields.Char('Destination')
    departure_date = fields.Date('Departure Date')
    arrival_date = fields.Date('Arrival Date')
    travel_id = fields.Many2one('hr.travel')
    travel_doc = fields.Binary('Document')
    file_name = fields.Char('File')


class HrAllowancesLine(models.Model):
    _name = 'hr.allowances.line'

    name = fields.Char(string='Name')
    allowance_head_id = fields.Many2one(
        'hr.travel.allowance.head', string='Allowance Head')
    done_by = fields.Selection([('company', 'Company'),
                                ('employee', 'Employee'),
                                ('not_applicable', 'Not Applicable')], string='Borne by')
    based_on = fields.Selection([('country', 'Country'),
                                 ('country_group', 'Country Group')],
                                string='Based on', default='country')
    amount = fields.Float(string='Amount')
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency',
                                  default=lambda self: self.env.user.currency_id)
    travel_id = fields.Many2one(
        'hr.travel', string='Travel', ondelete='cascade')


class HRExpenses(models.Model):
    _inherit = 'hr.expense'

    travel_id = fields.Many2one('hr.travel', string="Travel Ref.")

class HRVisa(models.Model):
    _inherit = 'hr.visa'

    travel_id = fields.Many2one('hr.travel', 'Travel Details')


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    travel_ids = fields.One2many('hr.travel', 'employee_id',
                                 string='Travel Details')

    def action_travel_details(self):
        action = self.env.ref('bista_hr_travel.hr_travel_action')
        domain = [('employee_id', '=', self.id)]
        result = {
            'name': action.name,
            'type': action.type,
            'view_type': action.view_type,
            'view_mode': action.view_mode,
            'target': action.target,
            'context': self._context,
            'res_model': action.res_model,
            'domain': domain,
        }
        return result

class HrTravelAllowanceHead(models.Model):

    _name = 'hr.travel.allowance.head'
    _description = 'Allowance Head'

    name = fields.Char('Name')
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)


class HrTravelAllowance(models.Model):

    _name = 'hr.travel.allowance.configuration'
    _description = 'Allowance'

    name = fields.Char(string='Name')
    allowance_id = fields.Many2one(
        'hr.travel.allowance.head', string='Allowance Head')
    done_by = fields.Selection([('company', 'Company'),
                                ('employee', 'Employee'),
                                ('not_applicable', 'Not Applicable')], string='Borne by')
    based_on = fields.Selection([('country', 'Country'),
                                 ('country_group', 'Country Group')],
                                string='Based on', default='country')
    country_id = fields.Many2one('res.country', string='Country')
    country_group_id = fields.Many2one(
        'res.country.group', string='Country Group')
    job_id = fields.Many2one('hr.job', string='Designation')
    amount = fields.Float(string='Amount')
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency',
                                  default=lambda self: self.env.user.currency_id)
