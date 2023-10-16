# -*- encoding: utf-8 -*-
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class GratuityAdvancePayment(models.TransientModel):
    _name = "gratuity.advance.payment.wizard"
    
    journal_id = fields.Many2one('account.journal',string="Payment Journal")

    @api.multi
    def pay_gratuity_advance(self):
        """
        Used to pay gratuity advance for employee
        :return:
        """
        self.ensure_one()
        act_id = self._context.get('active_id')
        act_mdl = self._context.get('active_model')
        req_obj = self.env[act_mdl]
        gratuity_adv_line = req_obj.browse(act_id)
        if gratuity_adv_line.advance_amount <= 0.0:
            raise ValidationError("Amount to pay is not valid.")
        debit_vals = {
            'debit': gratuity_adv_line.advance_amount,
            'credit': 0.0,
            'account_id': gratuity_adv_line.employee_id.company_id.gratuity_journal_id. \
                                  default_credit_account_id.id or False,
            'partner_id': gratuity_adv_line.employee_id.partner_id.id or False,
        }
        credit_vals = {
            'debit': 0.0,
            'credit': gratuity_adv_line.advance_amount,
            'account_id': self.journal_id.default_credit_account_id.id or False,
            'partner_id': gratuity_adv_line.employee_id.partner_id.id or False,
        }
        move_vals = {
            'journal_id': self.journal_id.id or False,
            'date': fields.date.today(),
            'state': 'draft',
            'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)],
            'ref': 'Gratuity Advance Payment'
        }
        move_ids = []
        for line in gratuity_adv_line.gtt_accrual_id.accrual_line_ids:
            move_ids.append(line.account_move_id.id)
        move = self.env['account.move'].create(move_vals)
        move.post()
        move_line = self.env['account.move.line'].search([('move_id', 'in', move_ids),
                                                          ('full_reconcile_id', '=', False)])
        lv_sal_mvl = self.env['account.move.line']
        reconcile_mvl = move.line_ids + move_line
        for line in reconcile_mvl:
            if line.account_id.user_type_id.type in \
                    ('receivable', 'payable'):
                lv_sal_mvl += line
        lv_sal_mvl.reconcile()
        gratuity_adv_line.account_move_id = move
        gratuity_adv_line.state = 'paid'
        
        
        