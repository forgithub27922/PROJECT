from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class LeaveEncashment(models.Model):
    _name = "leave.encashment"
    _rec_name = "employee_id"

    encash_date = fields.Date("Date", default=datetime.now().date())
    employee_id = fields.Many2one("hr.employee", "Employee")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('approved', 'Approved'),
        ('paid', 'Paid'), ('cancel', 'Cancel')], default="draft", readonly=True)
    allocation_ids = fields.Many2many("hr.holidays", "holidays_encashment_rel",
                                      'encashment_id', 'holidays_id', "Leaves")
    leaves_to_encash = fields.Float(string="Day's to Encash",
                                    compute='_get_no_of_encash_days',
                                    store=True)
    encash_amount = fields.Float(string="Encash Amount",
                                 compute='_get_no_of_encash_days',
                                 store=True)
    holiday_status_id = fields.Many2one('hr.holidays.status',
                                        string='Leave Type')
    type = fields.Selection([
        ('lapse_leaves_to_encash', 'Lapse Leaves to Encash'),
        ('lapse_and_encash', 'Lapse & Encash Leaves'),
    ], default="lapse_and_encash",)
    days_to_encash = fields.Float('Leaves to Encash')
    leaves_to_lapse = fields.Float('Leaves to Lapse')
    total_leave_type_days = fields.Float(string='Total days',
                                         compute='_compute_total_days')

    max_allowed = fields.Float(
        string='Max Leaves', related='holiday_status_id.maximum_leave_balance')
    max_leave_encash = fields.Float(
        string='Max Leaves to Encash',
        related='holiday_status_id.no_of_days_encash')
    
    leave_encashment_payment_mode = fields.Selection([('direct', 'Direct Payment'), ('salary', 'Salary Payment')], string="Payment Type", default="direct")
    account_move_id = fields.Many2one('account.move', string='Journal Entry', copy=False)
    is_payslip_payment = fields.Boolean(string='Pay from Payslip')
    payslip_id = fields.Many2one('hr.payslip', string="Payslip")
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)
    move_ids = fields.Many2many('account.move', 'leave_encashment_move_rel', string='Journal Entry', copy=False)
    eos_fnf_id = fields.Many2one('hr.termination.request', string="EOS F&F",copy=False)

    @api.onchange('holiday_status_id', 'max_allowed', 'max_leave_encash')
    def onchange_holiday_status(self):
        if self.holiday_status_id:
            if self.max_allowed > self.total_leave_type_days:
                self.days_to_encash = self.total_leave_type_days
                self.leaves_to_lapse = self.total_leave_type_days
            else:
                self.days_to_encash = self.total_leave_type_days - self.max_allowed
                self.leaves_to_lapse = self.total_leave_type_days - self.max_allowed 
            if self.days_to_encash > self.holiday_status_id.no_of_days_encash:
                self.days_to_encash = self.holiday_status_id.no_of_days_encash

    @api.depends('employee_id', 'holiday_status_id')
    def _compute_total_days(self):
        if self.type == 'lapse_and_encash':
            leaves_add = self.env['hr.holidays'].search([
                ('employee_id', '=', self.employee_id.id),
                ('holiday_status_id', '=', self.holiday_status_id.id),
                ('type', '=', 'add'),
                ('state', '=', 'validate')])
            leaves_remove = self.env['hr.holidays'].search([
                ('employee_id', '=', self.employee_id.id),
                ('holiday_status_id', '=', self.holiday_status_id.id),
                ('type', '=', 'remove'),
                ('state', '=', 'validate')])
            add_days = sum(
                    leave.number_of_days_temp for leave in leaves_add)
            take_days = sum(
                    leave.number_of_days_temp for leave in leaves_remove)
            self.total_leave_type_days = add_days - take_days

    @api.one
    @api.depends('allocation_ids')
    def _get_no_of_encash_days(self):
        if self.type == 'lapse_leaves_to_encash':
            leave_dict = {}
            for leave in self.allocation_ids:
                if leave.holiday_status_id.id in leave_dict:
                    days = \
                        float(leave_dict.get(leave.holiday_status_id.id)) + \
                        leave.number_of_days_temp
                    leave_dict.update({leave.holiday_status_id.id: days})
                else:
                    leave_dict.update({
                        leave.holiday_status_id.id: leave.number_of_days_temp})
            latest_days = 0.0
            holiday_status = self.env['hr.holidays.status']
            for leave_type_rec in holiday_status.browse(leave_dict.keys()):
                if leave_type_rec.id in leave_dict.keys():
                    latest_days += min(leave_type_rec.no_of_days_encash,
                                       leave_dict.get(leave_type_rec.id))
            self.leaves_to_encash = latest_days
            if self.employee_id and self.employee_id.contract_id:
#                 self.encash_amount = \
#                     latest_days * self.employee_id.contract_id.wage / 30
                self.encash_amount = round(latest_days * (self.employee_id.contract_id.wage * 12) / 365)

    @api.multi
    def action_open_journal_entries(self):
        '''
        Get Linked Journal Entry
        :return:
        '''
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Journal Entry'),
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'domain': [('id', 'in', self.move_ids.ids)],
            'res_id': self.move_ids.ids,
            'target': 'current',
        }

    @api.multi
    def action_cancel(self):
        for rec in self:
            if self.state in ['approved','paid']:
                if self.leave_encashment_payment_mode == 'salary':
                    raise UserError(_('You cannot cancel Leave Encashment which is paid from Payslip.'))
                else:
                    if not self.env['ir.module.module'].sudo().search([('name', '=', 'account_cancel'), ('state', '=', 'installed')]):
                        raise UserError(_("Needs To Install \'Cancel Journal Entries\' Module"))
                    for move_id in self.move_ids:
                        if move_id.journal_id.update_posted:
                            move_id.line_ids.remove_move_reconcile()
                            move_id.button_cancel()
                            move_id.with_context({'custom_move':True}).unlink()
                        else:
                            raise UserError(_(
                                "Goto Journal -> Adcanced Settings -> "
                                "Allow Cancelling Entries=True "))

            lapse_leave = self.env['hr.holidays'].search([('encashment_id', '=', rec.id)])
            if lapse_leave:
                lapse_leave.action_refuse()
                lapse_leave.action_draft()
                lapse_leave.unlink()
        self.write({'state':'cancel'})
        
    @api.multi
    def action_reset(self):
        self.write({'state':'draft'})
        
    @api.multi
    def action_approved(self):
        if self.type == 'lapse_leaves_to_encash':
            self.state = 'approved'
        if self.type == 'lapse_and_encash':
#             self.encash_amount = self.days_to_encash * self.employee_id.contract_id.wage / 30
            self.encash_amount = round(self.days_to_encash * (self.employee_id.contract_id.wage * 12) / 365)
        elif self.type == 'lapse_leaves_to_encash':
#             self.encash_amount = self.leaves_to_encash * self.employee_id.contract_id.wage / 30
            self.encash_amount = round(self.leaves_to_encash * (self.employee_id.contract_id.wage * 12) / 365)
        if self.type == 'lapse_and_encash' and self.holiday_status_id:
            max_leaves = self.holiday_status_id.maximum_leave_balance
            days = self.total_leave_type_days - max_leaves
            if self.days_to_encash > self.holiday_status_id.no_of_days_encash:
                raise ValidationError(
                    _('You cannot encash more then %s Leaves '
                      'as per Leave type Configuration'
                      % (self.holiday_status_id.no_of_days_encash)))
            if self.leaves_to_lapse <= 0:
                raise ValidationError(
                    _('Lapse leave can not be zero or more then Lapse Leaves.'))
            if self.days_to_encash > self.leaves_to_lapse:
                raise ValidationError(_('Encash days can not be greater then Lapse days'))
            else:
                holidays_obj = self.env['hr.holidays']
                name = 'Lapse Leave Created'
                leave_vals = {
                    'name': name,
                    'state': 'confirm',
                    'type': 'remove',
                    'holiday_status_id': self.holiday_status_id.id,
                    'employee_id': self.employee_id.id,
                    'number_of_days_temp': self.leaves_to_lapse,
                    'department_id':self.employee_id.department_id.id or False,
                    'lapse_leave': True,
                    'date_from': self.encash_date,
                    'date_to': self.encash_date,
                    'encashment_id' :self.id,
                    'company_id':self.company_id.id,
                }
                ctx = dict(self._context)
                ctx.update({'lapse_leave': True})
                new_holiday_rec = holidays_obj.create(leave_vals)
                new_holiday_rec.with_context(ctx).action_approve()
                if new_holiday_rec.holiday_status_id.double_validation:
                    new_holiday_rec.with_context(ctx).action_validate()
                self.leaves_to_encash = days - self.leaves_to_lapse
                self.state = 'approved'

                # Create encashment adjustment move
                self.crete_encashment_move(new_holiday_rec)

    @api.multi
    def action_confirm(self):
        self.state = 'confirm'

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state in ('paid', 'approved'):
                raise UserError(_('You cannot delete paid or approved '
                              'leave encashment.'))
        return super(LeaveEncashment, self).unlink()


    @api.multi
    def crete_encashment_move(self,holiday_rec):
        '''
            This method create JE for leave expenses adjustmment entry with unposted state.
            amount calculation like  = holidaye leave amount - encashment amount.
        '''
        diff_amount = abs(holiday_rec.leave_amount) - self.encash_amount
        if diff_amount:
            if not holiday_rec.holiday_status_id.leave_salary_journal_id:
                raise ValidationError(_('Please Configured Leave Salary Journal for %s type.' % (holiday_rec.holiday_status_id.name)))

            if not holiday_rec.holiday_status_id.leave_salary_journal_id.default_credit_account_id:
                raise ValidationError(_('Please configured credit/debit account for %s journal.' % (holiday_rec.holiday_status_id.leave_salary_journal_id.name)))

            if not holiday_rec.holiday_status_id.expense_account_id:
                raise ValidationError(_('Please configured expense account for %s type.' % (holiday_rec.holiday_status_id.name)))

            debit_vals = {
                    'debit': abs(diff_amount),
                    'account_id': holiday_rec.holiday_status_id.leave_salary_journal_id.default_credit_account_id.id,
                    'partner_id': self.employee_id.partner_id.id,
                    'name':'Leave Salary Adjustment Entry'
                    }
            credit_vals = {
                'credit': abs(diff_amount),
                'account_id': holiday_rec.holiday_status_id.expense_account_id.id,
                'partner_id': self.employee_id.partner_id.id,
                'analytic_account_id':self.employee_id.contract_id.analytic_account_id.id,
                'name':'Leave Salary Adjustment Entry'
            }
            move_vals = {
                'journal_id': holiday_rec.holiday_status_id.leave_salary_journal_id.id,
                'date': self.encash_date,
                'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)],
                'ref': 'Leave Salary Adjustment Entry'
            }
            move = self.env['account.move'].sudo(self.env.user.id).create(move_vals)
            self.write({'move_ids':[(4, move.id)]})
