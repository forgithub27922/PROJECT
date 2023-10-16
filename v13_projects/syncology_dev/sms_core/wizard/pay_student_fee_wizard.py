# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from odoo.tools.mail import append_content_to_html


class FeePaymentWizard(models.TransientModel):

    _name = 'student.fee.payment.wizard'
    _description = 'student.fee.payment.wizard'

    @api.model
    def default_get(self, field_list):
        res = super(FeePaymentWizard, self).default_get(field_list)
        res.update({
            'amount': self.env['student.fee'].search([('id','=',self._context.get('installment_id'))]).applied_fee,
        })
        return res
    
    @api.onchange('payment_date','amount')
    def onchange_payment_date(self):
        fee_list =[]
        if self.operation_type == 'multiple_records' and self.mode == 'pay_student_fee':
            self.student_fee_ids = None
            std_fee_ids = self.env['student.fee'].search([('fee_policy_line_id', '=', self.installment_id.id),('status', '=', 'unpaid')])
        elif self.operation_type == 'multiple_records' and self.mode == 'refund_student_fee':
            self.student_fee_ids = None
            std_fee_ids = self.env['student.fee'].search([('fee_policy_line_id', '=', self.installment_id.id),('status', '=', 'paid')])
        elif self.operation_type == 'single_record' and self.mode == 'pay_student_fee':
            self.student_fee_ids = [(6, 0, self.student_fee_ids.ids)]
            std_fee_ids = self.student_fee_ids
        elif self.operation_type == 'single_record' and self.mode == 'refund_student_fee':
            self.student_fee_ids = [(6, 0, self.student_fee_ids.ids)]
            std_fee_ids = self.student_fee_ids
        if self.mode == 'pay_student_fee':
            new_status = 'paid'
        elif self.mode == 'refund_student_fee':
            new_status = 'refunded'
            
        if not self.mode =='update_fee_register':
            for fee in std_fee_ids:
                fee_dictt = (0, 0, {'parent_id': self.id ,'student_id':fee.student_id.id, 'std_fee_id': fee.id , 'status':new_status,'payment_date': self.payment_date ,'applied_fee':self.amount, 'due_date': fee.due_date,'is_overdue':fee.is_overdue})
                fee_list.append(fee_dictt)

        self.student_fee_ids = fee_list
        return
    
    installment_id = fields.Many2one('fee.policy.line',string='Installment')
    payment_date = fields.Date('Payment Date')
    mode = fields.Selection([('update_fee_register','Update Fee Register'),('pay_student_fee','Pay Students Fee'),('refund_student_fee','Refund Students Fee')],string = 'Action')
    student_fee_ids = fields.One2many('fee.payment.wizard.line','parent_id', string='Student Fee')
    operation_type = fields.Selection([('single_record','Single Record'),('multiple_records','Multiple Records')], default='multiple_records',string = 'Operation')
    amount = fields.Float(string='Amount')
    journal_id = fields.Many2one('account.journal',string = 'Journal')
    from_account = fields.Many2one('account.account',string = 'From Account')
    to_account = fields.Many2one('account.account', string='To Account')
    

    def student_fee_payment(self):
        if len(self.student_fee_ids)<1:
            raise UserError(_('No unpaid records found'))

        listt = []
        mail_ids = []
        mail_pool = self.env['mail.mail']
        student_fee_obj = self.env['student.fee']
        for fee in self.student_fee_ids:
            dictt = {'std_fee_id':fee.std_fee_id.id,'payment_date':fee.payment_date}
            listt.append(dictt)
        call = self.env['student.fee'].pay_student_fee_cm(listt)
        create_entry = True
        std_fee = self.env['student.fee'].browse(self._context.get('installment_id'))
        if self.mode == 'pay_student_fee':
            if not std_fee.applied_fee:
                create_entry = False
            else:
                from_account = std_fee.fee_policy_line_id.from_account.id
                to_account = std_fee.fee_policy_line_id.to_account.id
                journal_id = std_fee.fee_policy_line_id.journal_id.id
                label_name = 'Payment'
                debit_line_vals = {
                    'name': label_name,
                    'debit': std_fee.applied_fee or 0.0,
                    'credit': 0.0,
                    'account_id': from_account,
                }
            subject = 'Fee Payment'
            body_html = """<div>
            <p>Dear Mr.""" + str(std_fee.student_id.first_name) + \
                        ' ' + str(std_fee.student_id.middle_name) + \
                        ' ' + str(std_fee.student_id.second_middle_name) + \
                        ' ' + str(std_fee.student_id.last_name) + """,<br/>
            We kindly confirm that an amount of """ + str(self.amount) + \
                        """ has been settled for """ + str(std_fee.fee_type_id.name) + \
                        """ on """ + str(self.payment_date) + """<br/></p>
            </div>"""
        elif self.mode == 'refund_student_fee':
            from_account = self.from_account.id
            to_account = self.to_account.id
            journal_id = self.journal_id.id
            std_fee.status = 'refunded'
            label_name = 'Refund'
            debit_line_vals = {
                'name': label_name,
                'debit': self.amount or 0.0,
                'credit': 0.0,
                'account_id': from_account,
            }
            subject = 'Fee Refund'
            body_html = """<div>
            <p>Dear Mr.""" + str(std_fee.student_id.first_name) + \
                        ' ' + str(std_fee.student_id.middle_name) + \
                        ' ' + str(std_fee.student_id.second_middle_name) + \
                        ' ' + str(std_fee.student_id.last_name) + """,<br/>
            We kindly confirm that an amount of """ + str(self.amount) + \
                        """ has been refunded for """ + str(std_fee.fee_type_id.name) + \
                        """ on """ + str(self.payment_date) + """<br/>
            If the payment was done through a credit card, then the refund shall take place within 10 working days
            </p></div>"""
        if create_entry:
            credit_line_vals = debit_line_vals.copy()
            credit_line_vals['debit'] = debit_line_vals['credit']
            credit_line_vals['credit'] = debit_line_vals['debit']
            credit_line_vals['account_id'] = to_account
            vals = {
                'type': 'entry',
                'date':  std_fee.payment_date or datetime.today(),
                'state': 'draft',
                'ref': self.installment_id.name,
                'journal_id': journal_id,
                'line_ids': [(0, 0, debit_line_vals), (0, 0, credit_line_vals)]
            }
            if std_fee and std_fee.account_id and self.mode == 'refund_student_fee':
                vals.update({'name': 'R-' + std_fee.account_id.name or ''})
            account_id = self.env['account.move'].sudo().create(vals)
            account_id.action_post()
            std_fee.account_id = account_id.id
        std_fee.student_id.payment_status = 'paid'
        transport_student = self.env['register.student.transport'].sudo().search([('student_id', '=', std_fee.student_id.id),('installment_id', '=', std_fee.fee_policy_line_id.id), ('state', '=', 'draft')])
        # To check fee type with configuration fee type if equal then change the tranport state registred
        company_id = self.env.company
        if std_fee.fee_type_id.id == company_id.transport_fee_type_id.id:
            transport_student.state = 'registered'
            transport_student.set_regno()
        unpaid_records = student_fee_obj.search(
        [('student_id', '=', std_fee.student_id.id), ('status', '=', 'unpaid'),('id','!=',std_fee.id)])
        if unpaid_records:
            installment_list = '<br/> We would also like to kindly remind you of the other due amounts: <br/>'
            installment_list_lines = ''
            unpaid_records_total_amount = 0.0
            for fee in unpaid_records:
                installment_list_lines = installment_list_lines + str(fee.total_amount) + \
                                         ' for ' + str(fee.fee_type_id.name) + \
                                         ' before ' + str(fee.due_date) + '<br/>'
                unpaid_records_total_amount = unpaid_records_total_amount + fee.total_amount
            body_html = body_html + installment_list + installment_list_lines
            body_html = body_html + '<br/>Total amount: ' + str(unpaid_records_total_amount)
        body_html = body_html + '<br/> Thank you for taking the time to look into this. We wish you a pleasant day.'
        if std_fee.student_id.father_email:
            mail_ids.append(std_fee.student_id.father_email)
        if std_fee.student_id.mother_email:
            mail_ids.append(std_fee.student_id.mother_email)
        if std_fee.student_id.guardian_email:
            mail_ids.append(std_fee.student_id.guardian_email)
        values = ({'email_to': ','.join(mail_ids), 'body_html': body_html, 'body': body_html, 'subject': subject})
        msg_id = mail_pool.create(values)
        if msg_id:
            msg_id.send()

    def update_student_fee_register(self):
        call = self.env['fee.policy.line'].update_student_fee_register(self.installment_id, 'Manual Process')
        return


class FeePaymentWizardline(models.TransientModel):

    _name = 'fee.payment.wizard.line'
    _description = 'fee.payment.wizard.line'
    
    parent_id = fields.Many2one('student.fee.payment.wizard',string='Parent')
    std_fee_id = fields.Many2one('student.fee',string='Fee')
    student_id = fields.Many2one('academic.student',string='Student')
    payment_date = fields.Date('Payment Date')
    fee_date = fields.Date('Fee Date',tracking=True)
    due_date = fields.Date('Due Date',tracking=True)
    total_amount = fields.Float(string = 'Fee',default=0.0,tracking=True)
    applied_fee = fields.Float(string='Fee Applied')
    status = fields.Selection([('unpaid', 'Unpaid'),('paid', 'Paid'),('refunded','Refunded'), ('cancelled', 'Cancelled')], string='Status',tracking=True)
    is_overdue = fields.Boolean(string ='Overdue')