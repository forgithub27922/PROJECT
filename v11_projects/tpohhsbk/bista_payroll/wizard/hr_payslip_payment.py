# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class HrPayslipPayment(models.TransientModel):
    _name = 'hr.payslip.payment'
    _description = "Payslip Payment"

    @api.model
    def default_get(self, fields):
        context = dict(self._context)
        res = super(HrPayslipPayment, self).default_get(fields)
        payslip_obj = self.env['hr.payslip']

        payslip_records = payslip_obj
        if context.get('active_model') == 'hr.payslip':
            payslip_records = payslip_obj.browse(context.get('active_ids'))
        if context.get('active_model') == 'hr.payslip.run':
            payslip_records = payslip_obj.search([('payslip_run_id', '=',
                                                   context.get('active_id'))])

        total = 0.0
        payslip_records = payslip_records.filtered(lambda l:l.state == 'done')
        for payslip in payslip_records:
            total += payslip.net_amount

        if 'transaction_nbr' in fields:
            res.update({'transaction_nbr': len(payslip_records)})
        if 'total' in fields:
            res.update({'total': total})
        if 'dummy_total' in fields:
            res.update({'dummy_total': total})
        return res

#     journal_id = fields.Many2one('account.journal', 'Salary Journal')
    transaction_nbr = fields.Integer('# of Transaction', readonly=True)
    total = fields.Float('Total', readonly=True)
    dummy_total = fields.Float('Total')
    date = fields.Date('Date', default=fields.date.today())
    payment_line_ids = fields.One2many('hr.payslip.payment.line', 'payment_id', string="Payment Lines")

    @api.multi
    def action_to_reconcile(self):
        self.ensure_one()
        context = dict(self._context)
        payslip_obj = self.env['hr.payslip']
        aml_obj = self.env['account.move.line']

        payslip_records = payslip_obj
        batch_slip_obj = self.env['hr.payslip.run']
        batch_slip_records = self.env['hr.payslip.run']
        if context.get('active_model') == 'hr.payslip':
            payslip_records = payslip_obj.browse(context.get('active_ids'))
        if context.get('active_model') == 'hr.payslip.run':
            payslip_records = payslip_obj.search([('payslip_run_id', '=', context.get('active_id'))])
            batch_slip_records = batch_slip_obj.browse(context.get('active_id'))

        if any(not (line.journal_id.default_debit_account_id or line.journal_id.default_credit_account_id) for line in self.payment_line_ids):
            raise ValidationError(_("Configured Journal Default Credit and Debit Account!"))

        move_lines = []
        payslip_total_amount = 0.00

        active_move = payslip_records[0].move_id
        journal_rec = payslip_records[0].journal_id
        if journal_rec and not (journal_rec.default_debit_account_id or journal_rec.default_credit_account_id):
            raise ValidationError(_('Journal have should be configured Credit and Debit Account.!'))

        jrnl_debit = journal_rec.default_debit_account_id.id

        for payslip in payslip_records:
            payslip_total_amount += payslip.net_amount

        name = batch_slip_records.name if batch_slip_records else payslip_records[0].name

        for line in self.payment_line_ids:
            credit_vals = {
                'name': 'Salary Paid',
                'debit': 0.0,
                'credit': abs(line.amount),
                'account_id':line.journal_id.default_credit_account_id.id,
            }
            move_lines.append((0, 0, credit_vals))

        debit_vals = {
                'name': name,
                'debit': abs(payslip_total_amount),
                'credit': 0.0,
                'account_id': jrnl_debit,
            }
        move_lines.append((0, 0, debit_vals))

        vals = {
            'journal_id': journal_rec.id,
            'date': self.date or fields.date.today(),
            'state': 'draft',
            'line_ids': move_lines,
            'ref': 'Pay Salary'
        }
        move = self.env['account.move'].sudo().create(vals)
        for line in self.payment_line_ids.sudo():
            for payslip in payslip_records.filtered(lambda l:l.employee_id.journal_id.id == line.journal_id.id):
                payslip.write({'is_paid': True, 'state': 'paid',
                               'employee_payment_journal_id':line.journal_id.id,
                               'account_move_id': move.id})

        batch_slip_records.write({'account_move_id': move.id, 'state': 'paid'})

        return True


class hr_payslip_payment_line(models.TransientModel):
    _name = 'hr.payslip.payment.line'
    _description = "Payslip Payment Line"

    payment_id = fields.Many2one('hr.payslip.payment', string="Payment")
    journal_id = fields.Many2one('account.journal', string="Journal")
    amount = fields.Float(string="Amount")

