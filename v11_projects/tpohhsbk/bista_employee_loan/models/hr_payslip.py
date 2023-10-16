from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.multi
    def action_set_to_draft(self):
        for payslip in self:
            for line in payslip.line_ids:
                if line.code == 'LOAN' and line.salary_rule_id.code == 'LOAN' \
                    and line.salary_rule_id.category_id.code == 'DED':
                    loans = self.env['hr.employee.loan'].search([
                    ('employee_id', '=', payslip.employee_id.id),
                    ('state', 'in', ['approved', 'done'])])
                    for loan in loans:
                        all_installment = self.env['loan.installments'].search([
                            ('due_date', '>=', payslip.date_from),
                            ('due_date', '<=', payslip.date_to),
                            ('state', '=', 'done'),
                            ('loan_id', '=', loan.id)])
                        all_installment.write({'state':'draft'})
                        if all(loan_statement.state != 'done' for loan_statement in loan.loan_installment_ids):
                            loan.write({'state': 'approved'})
        res = super(HrPayslip, self).action_set_to_draft()
        return res

    @api.multi
    def do_loan_confirm(self):
        if not self.contract_id:
            raise ValidationError(_('Please define contract for \
                                    employee %s ' % 
                                    self.employee_id.name))
        for line in self.line_ids:
            if line.code == 'LOAN' and line.salary_rule_id.code == 'LOAN' \
                    and line.salary_rule_id.category_id.code == 'DED':
                loans = self.env['hr.employee.loan'].search([
                    ('employee_id', '=', self.employee_id.id),
                    ('state', 'in', ['approved', 'done'])])
                for loan in loans:
                    all_installment = self.env['loan.installments'].search([
                        ('due_date', '>=', self.date_from),
                        ('due_date', '<=', self.date_to),
                        ('state', 'not in', ('reject', 'done')),
                        ('loan_id', '=', loan.id)])
                    for installment in all_installment:
                        installment.write({'state': 'done',
                               'paid_date': self.date,
                               'paid_amount': installment.amount})
#                         self.action_move_create(installment)
                    if all(loan_statement.state == 'done' for loan_statement in loan.loan_installment_ids):
                        loan.write({'state': 'done'})

    @api.multi
    def action_payslip_done(self):
        """Calculate payroll based onloan install if employee has issued
                loan in current month. For e.g. Payslip date:
                 5/1/2018-5/31/2018
                and have loan installment due date between
                 Payslip date: 5/1/2018-5/31/2018 ."""
        if not self.contract_id:
            raise ValidationError(_('Please define contract for \
                                    employee %s ' % 
                                    self.employee_id.name))
        for line in self.line_ids:
            if line.code == 'LOAN' and line.salary_rule_id.code == 'LOAN' \
                    and line.salary_rule_id.category_id.code == 'DED':
                loans = self.env['hr.employee.loan'].search([
                    ('employee_id', '=', self.employee_id.id),
                    ('state', 'in', ['approved', 'done'])])
                for loan in loans:
                    all_installment = self.env['loan.installments'].search([
                        ('due_date', '>=', self.date_from),
                        ('due_date', '<=', self.date_to),
                        ('state', 'not in', ('reject', 'done')),
                        ('loan_id', '=', loan.id)])
                    for installment in all_installment:
                        installment.write({'state': 'done',
                               'paid_date': self.date,
                               'paid_amount': installment.amount})
#                         self.action_move_create(installment)
                    if all(loan_statement.state == 'done' for loan_statement in loan.loan_installment_ids):
                        loan.write({'state': 'done'})
        return super(HrPayslip, self).action_payslip_done()

    @api.multi
    def action_move_create(self, installment):
        move = self.env['account.move'].create({
            'journal_id': installment.loan_id.loan_journal_id.id if
            installment.loan_id.loan_journal_id else False,
            'company_id': self.env.user.company_id.id if
            self.env.user.company_id else False,
            'date': installment.due_date,
            'ref': 'Installment %s' % installment.loan_id.name,
            'name': '/',
        })
        if move:
            move_line_lst = self._prepare_move_lines(move, installment)
            move.line_ids = move_line_lst
            installment.write({'state': 'done',
                               'paid_date': datetime.now().date(),
                               'paid_amount': installment.amount,
                               'residual': 0.0})
            installment.loan_id.write({'move_ids':[(4, move.id)]})
#             move.post()

    def _prepare_move_lines(self, move, installment):
        move_lst = []
        partner = (installment.employee_id.partner_id and \
                  installment.employee_id.partner_id.id) or \
                  (installment.employee_id.user_id and
                   installment.employee_id.user_id.partner_id.id)
        generic_dict = {
            'name': self.name,
            'company_id': self.env.user.company_id.id if
            self.env.user.company_id else False,
            'currency_id': self.env.user.company_id.currency_id.id if
            self.env.user.company_id and
            self.env.user.company_id.currency_id else False,
            'date_maturity': installment.due_date,
            'journal_id': installment.loan_id.loan_journal_id.id if
            installment.loan_id.loan_journal_id else False,
            'date': installment.due_date,
            'partner_id': partner or False,
            'quantity': 1,
            'move_id': move.id,
        }
        loan_journal = installment.loan_id \
                       and installment.loan_id.loan_journal_id
        credit_entry_dict = {
            'account_id':
                loan_journal and loan_journal.default_credit_account_id and
                loan_journal.default_credit_account_id.id or False,
            'credit': installment.amount,
            'partner_id': partner or False,
        }
        loan_rule_account = False
        for line in self.line_ids:
            if line.code == 'LOAN':
                loan_rule_account = line.salary_rule_id and \
                                    line.salary_rule_id.account_debit and \
                                    line.salary_rule_id.account_debit.id
        if not loan_rule_account:
            loan_rule_account = installment.loan_id and \
                                installment.loan_id.debit_account_id and \
                                installment.loan_id.debit_account_id.id \
                                or False
        debit_entry_dict = {
            'account_id': loan_rule_account,
            'debit': installment.amount,
        }
        debit_entry_dict.update(generic_dict)
        credit_entry_dict.update(generic_dict)
        move_lst.append((0, 0, debit_entry_dict))
        move_lst.append((0, 0, credit_entry_dict))
        return move_lst

    @api.multi
    def compute_sheet(self):
        if self._context.get('from_batch'):
            for payslip in self:
                payslip._calculate_installment_amount()
        return super(HrPayslip, self).compute_sheet()

    @api.one
    @api.depends('date_from', 'date_to')
    def _calculate_installment_amount(self):
        self.installment_amount = 0.00
        loans = self.env['hr.employee.loan'].search([
            ('employee_id', '=', self.employee_id.id),
            ('state', 'in', ['approved', 'done'])])
        for loan in loans:
            install_ment = self.env['loan.installments'].search([
                ('due_date', '>=', self.date_from),
                ('due_date', '<=', self.date_to),
                ('state', 'not in', ('reject', 'done')),
                ('loan_id', '=', loan.id)])
            for install in install_ment:
                self.installment_amount += install.amount

    installment_amount = fields.Float(string='Installment Amount',
                                      compute='_calculate_installment_amount',
                                      store=True)


class hr_payslip_run(models.Model):
    _inherit = 'hr.payslip.run'

    @api.multi
    def confirm_payslip(self):
        res = super(hr_payslip_run, self).confirm_payslip()
        for payslip in self.slip_ids:
            payslip.do_loan_confirm()
        return res
