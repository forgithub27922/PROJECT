from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PettyCash(models.Model):
    _name = 'petty.cash'
    
    name = fields.Char(string="Name", default="New")
    employee_id = fields.Many2one('hr.employee',string="Employee", required=True)
    partner_id = fields.Many2one(related='employee_id.partner_id',string="Partner")
    amount = fields.Float(string="Amount")
    date = fields.Date(string="Date", required=True)
    state = fields.Selection([
                            ('draft', 'Draft'),
                            ('request', 'Requested'),
                            ('approve_by_manager', 'Approved By Manager'),
                            ('approve_by_hr', 'Approved By HR'),
                            ('approve_by_finance', 'Approved By Finance'),
                            ('paid', 'Paid'),
                            ('reconciled', 'Reconciled')],
                            string="State", default='draft', copy=False)
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  related='company_id.currency_id',
                                  store=True)
    notes = fields.Text(string="Notes")
    journal_id = fields.Many2one('account.journal', string="Journal")
    move_id = fields.Many2one('account.move', string="Accounting Entry")
    account_id = fields.Many2one('account.account', string="Account")
    
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('petty.cash') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('petty.cash') or _('New')
        result = super(PettyCash, self).create(vals)
        return result
    
    @api.multi
    def action_request(self):
        self.write({'state': 'request'})
        
    @api.multi
    def action_approve_by_manager(self):
        if self.env.user.id != self.employee_id.parent_id.user_id.id:
            raise UserError("Only employee's manager can approve this.")
        self.write({'state': 'approve_by_manager'})
        
    @api.multi
    def action_approve_by_hr(self):
        hr_manager_ids = self.env.ref('hr.group_hr_manager').users.ids
        if self.env.user.id not in hr_manager_ids:
            raise UserError("Only HR manager can perform this action.")
        self.write({'state': 'approve_by_hr'})


    @api.multi
    def action_approve_by_finance(self):
        account_manager_ids = self.env.ref('account.group_account_manager').users.ids
        if self.env.user.id not in account_manager_ids:
            raise UserError("Only HR finance can approve this.")
        self.write({'state': 'approve_by_finance'})

    @api.multi
    def action_pay_petty_cash(self):
        account_move = self.env['account.move']
        move_lines = [
                    (0, 0, {
                        'name': self.name, # a label so accountant can understand where this line come from
                        'debit': self.amount, # amount of debit
#                         'credit': self.credit, # amount of credit
                        'account_id': self.journal_id.default_debit_account_id.id, # account 
                        'date': self.date,
                        'partner_id': self.partner_id.id, # partner if there is one
                        'currency_id': self.currency_id.id
                    }),
                    (0, 0, {
                        'name': self.name,
#                         'debit': debit, 
                        'credit': self.amount,
                        'account_id': self.account_id.id,
#                         'analytic_account_id': context.get('analytic_id', False),
                        'date': self.date,
                        'partner_id': self.partner_id.id,
                        'currency_id': self.currency_id.id
                    })
                ]

        # Create account move
        new_move = self.env['account.move'].create({
                        'journal_id': self.journal_id.id, # journal ex: sale journal, cash journal, bank journal....
                        'date':self.date,
                        'state': 'draft',
                        'line_ids': move_lines, # this is one2many field to account.move.line
                    })
        self.move_id = new_move.id 
        
        