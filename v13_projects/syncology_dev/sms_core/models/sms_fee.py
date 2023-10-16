# -*- coding: utf-8 -*-
from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
import requests, json
from datetime import datetime, timedelta
from datetime import datetime
from datetime import date
from _ast import Try
from email.policy import default
from odoo.addons.test_convert.tests.test_env import field
import string
from pickletools import string1


class FeePolicyLine(models.Model):
    _name = 'fee.policy.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'fee.policy.line'
    _rec_name = 'installment_no'
    
    def write(self, vals):
        super(FeePolicyLine, self).write(vals)
        #self.update_student_fee_register()
        
        return
    
    def unlink(self):
        for fr in self:
            
            rec = self.env['student.fee'].search([('fee_policy_line_id','=',fr.id)])
            print("unlink called",len(rec))
            if len(rec)>0:
                raise UserError(_('Fee Installment cannot be deleted as it applied on some students'))
        return

    def update_student_fee_register(self,policy_lin_rec,call_method):
        """"
        This method will be updated by cron job also by button click
        """
        student_ids = self.env['academic.student'].search([('state', '=', 'admitted')])
        exists_count = 0
        new_records_count = 0
        for std in student_ids:
            emp_child = 0
            sibling_disc = 0

            exists = self.env['student.fee'].search([('student_id','=',std.id),('fee_policy_line_id','=',policy_lin_rec.id)])
            print("exists..",exists)
            if exists:
                if exists.status == 'unpaid':
                    dictt = {
                            'fee_date': policy_lin_rec.date,
                            'due_date': policy_lin_rec.due_date,
                            'total_amount': policy_lin_rec.amount,
                            'sibling_disc': sibling_disc,
                            'emp_chil_disc':emp_child
                            }
                    update = exists[0].write(dictt)
            elif not exists:
                new = self.env['student.fee'].create({
                        'student_id': std.id,
                        'fee_date': policy_lin_rec.date,
                        'due_date': policy_lin_rec.due_date,
                        'total_amount': policy_lin_rec.amount,
                        'sibling_disc': sibling_disc,
                        'emp_chil_disc':emp_child,
                        'fee_policy_line_id': policy_lin_rec.id,
                        'status': 'unpaid',
                        })
                print("++++++++ Not Exist ++++++++")
                if new:
                    new_records_count = new_records_count + 1
                    std.message_post(body='New Fee record inserted for '+str(policy_lin_rec.name)+" via a"+str(call_method))
            else:
                exists_count = exists_count +1 
                std.message_post(body='Fee Register updated for '+str(policy_lin_rec.name)+" via a"+str(call_method))
                exists[0].write({'due_date':policy_lin_rec.due_date,'total_amount':policy_lin_rec.amount,'emp_chil_sibling_disc':disc_amt})
        #self.message_post(body='Updating Student Fee Register for '+str(self.name)+'\nTotal '+str(len(student_ids))+' active students found.'+str(exists)+' already updated,'+str()+' New Fee records created.')

        return
    
    
    def call_warning_email_wizard(self):
        student_ids = self.env['academic.student'].search([('state', '=', 'admitted')])
        print("check that rec exist ++++++ ", student_ids)
        
        if student_ids:
            form_id = self.env.ref('sms_core.view_send_fee_overdue_email_wizard', False)
            return {
            'name': 'Send Warning Email',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'fee.overdue.warning.email.wizard',
            'view_id'   : form_id.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context'   :{
                'default_installment_id':self.id,
                'default_intallment_name':self.name,
                'default_warning_date':self.warning_email_date,
                'default_due_date':self.due_date,
                'default_student_ids':student_ids.ids,
                          }}
    
    def call_payment_fee_wizard(self):
        std_fee_ids = self.env['student.fee'].search([('fee_policy_line_id', '=', self.id),('status', '=', 'unpaid')])
        print("check that rec exist ++++++ ", std_fee_ids)
        
        if std_fee_ids:
            form_id = self.env.ref('sms_core.view_student_fee_payment_wizard', False)
            return {
            'name': 'Pay Student Fee',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'student.fee.payment.wizard',
            'view_id'   : form_id.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context'   :{
                'default_installment_id':self.id,
                'default_student_fee_ids':std_fee_ids.ids,
                          }}



    name = fields.Char(string='Fee')
    installment_no = fields.Char('Installment No', tracking=True, store=True)
    fee_type_id = fields.Many2one('fee.type', 'Fee Type')
    date = fields.Date('Fee Date')
    warning_email_date = fields.Integer(string='Days before Due Warning Email')
    due_date = fields.Date('Due Date')
    amount = fields.Float('Amount')
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True,  default=lambda self: self.env.company.currency_id)
    total_fee_charged = fields.Monetary('Total Fee', compute = 'compute_policyline_fees',currency_field='currency_id', help="Fee charged against student. Without discount")
    applied_fee = fields.Monetary('Applied Fee',currency_field='currency_id',  help="Fee charged against student. After Discount")
    discount_given = fields.Monetary('Discount Given', currency_field='currency_id', help="Total discount diven against this installment.Showing for paid fee only")
    collections = fields.Monetary('Collections', currency_field='currency_id', help="Collections")
    outsandings = fields.Monetary('Fee Balance',  currency_field='currency_id',help="Fee still not paid.")
    student_fee_ids = fields.One2many('student.fee', 'fee_policy_line_id', string="Student Fee")
    state = fields.Selection([('draft', 'Draft'), ('post', 'Post')], 'State', default='draft')
    journal_id = fields.Many2one('account.journal', 'Journal')
    from_account = fields.Many2one('account.account', 'From Account')
    to_account = fields.Many2one('account.account', 'To Account')
    academic_student_installment_ids = fields.One2many('academic.student.installment', 'fee_policy_line_id',
                                                       string="Student Fee")

    def action_post(self):
        return {
            'name': 'Post Fee Installments',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'post.fee.installment.wizard',
            'target': 'new'
        }

    def action_set_to_draft(self):
        if not self.academic_student_installment_ids:
            self.state = 'draft'
        else:
            raise ValidationError(_('You can reset the instalment to draft which has no students!'))

    def unlink(self):
        if self.state == 'post':
            raise UserError(_('Record cannot be deleted in Post State.'))
        else:
            rec = super(FeePolicyLine, self).unlink()
        return rec

class FeeType(models.Model):
    _name = 'fee.type'
    _description = 'Fee Type'

    name = fields.Char('Name')
    code = fields.Char('Code')
    
class StudentFee(models.Model):
    _name = 'student.fee'
    _description = 'student.fee'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def cron_warning_email(self):
        """
        This method is called, by a cron job to send warning email to student.
        """
        fee_ids = self.env['student.fee'].search([('status','=','unpaid'),('is_overdue','=',True)])
        self.overdue_warning_email(fee_ids)
    
    def overdue_warning_email(self,fee_ids):
        """"
        This is central method it will send warning email to guardians if fee overdue date
        passed created by ------- Sohail 17-June-2021
        Called from 
        1. Wizard ----> warning email wizard,
        2. Cron Job ----> called from cron job with button click
        """
        sendingData = []
        recipientData = []
        today = datetime.now()
        current_month = today.strftime("%m")
        current_year = today.strftime("%Y")
        
        for f in fee_ids:
            if f.status == 'unpaid':
                info = {
                    "std_name": f.student_id.full_name if f.student_id.full_name else '',
                    "installment_id": f.name if f.name else '',
                    "name": f.name if f.name else '',
                    "amount": f['total_amount'] if f['total_amount'] else '',
                    "due_date": f['due_date'] if f['due_date'] else '',
                }
                sendingData.append(info)
                if len(sendingData) > 0:
                    if f.student_id.father_email:
                        recipientData.append(f.student_id.father_email)
                    if f.student_id.mother_email:
                        recipientData.append(f.student_id.mother_email)
                    if f.student_id.legal_guardian != 'father_is_legal_guardian':
                        if f.student_id.guardian_email:
                            recipientData.append(f.student_id.guardian_email)

                try:
                    template = self.env.ref('sms_core.due_template_email')
                    email_value = {'email_to': ','.join(recipientData), 'email_from': self.env.user.email or '',
                                   'subject': 'Warning Email: ' + str(sendingData[0]['std_name']) + ' ,Payment Overdue'}
                    template.send_mail(f.id, email_values=email_value, force_send=True)
                    recipientData = []
                    sendingData = []

                except Exception as e:
                    raise ValidationError(e)
        
        return
    
    
    
    
    def compute_name(self):
        for stfee in self:
            stfee.name = stfee.fee_policy_line_id.installment_no
        return
    
    def get_final_applied_fee(self):
        for stfee in self:
            discounts = stfee.sibling_disc +stfee.emp_chil_disc + stfee.cash_discount
            stfee.applied_fee = stfee.total_amount - discounts 
        return
    
    def find_is_overdue(self):
        for stfee in self:
            today = date.today()
            if stfee.status =='unpaid':
                if str(today) > str(stfee.due_date):
                    stfee.is_overdue = True
                elif str(today) <= str(stfee.due_date):
                    stfee.is_overdue = False
            elif stfee.status =='paid':
               stfee.is_overdue = False
            elif stfee.status =='refunded':
               stfee.is_overdue = False
        return
    
    def call_fee_payment_wizard(self):
        std_fee_ids = self.env['student.fee'].search([('id', '=', self.id),('status', '=', 'unpaid')])
        wiz_lines = [(0, 0, {'student_id':std_fee_ids.student_id.id, 'std_fee_id': std_fee_ids.id , 'status':'unpaid','payment_date':None ,'applied_fee':std_fee_ids.applied_fee, 'due_date': std_fee_ids.due_date,'is_overdue':std_fee_ids.is_overdue})]
        wiz = self.env['student.fee.payment.wizard'].create({'mode':'pay_student_fee','operation_type':'single_record','installment_id': self.fee_policy_line_id.id, 'student_fee_ids': wiz_lines})
            
        if std_fee_ids:
            form_id = self.env.ref('sms_core.view_student_fee_payment_wizard', False)
            return {
            'name': 'Pay Student Fee',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'student.fee.payment.wizard',
            'view_id'   : form_id.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': wiz.id,
            'context'   :{
                'default_installment_id':self.fee_policy_line_id.id,
                          }
            }

    def call_refund_fee_wizard(self):
        std_fee_ids = self.env['student.fee'].search([('id', '=', self.id), ('status', '=', 'paid')])
        wiz_lines = [(0, 0, {'student_id': std_fee_ids.student_id.id, 'std_fee_id': std_fee_ids.id, 'status': 'paid',
                             'payment_date': None, 'applied_fee': std_fee_ids.applied_fee,
                             'due_date': std_fee_ids.due_date, 'is_overdue': std_fee_ids.is_overdue})]
        wiz = self.env['student.fee.payment.wizard'].create(
            {'mode': 'refund_student_fee', 'operation_type': 'single_record', 'installment_id': self.fee_policy_line_id.id,
             'journal_id':self.fee_policy_line_id.journal_id.id,'from_account':self.fee_policy_line_id.to_account.id,
             'to_account':self.fee_policy_line_id.from_account.id,'student_fee_ids': wiz_lines})

        if std_fee_ids:
            form_id = self.env.ref('sms_core.view_student_fee_payment_wizard', False)
            return {
                'name': 'Refund Student Fee',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'student.fee.payment.wizard',
                'view_id': form_id.id,
                'type': 'ir.actions.act_window',
                'target': 'new',
                'res_id': wiz.id,
                'context': {
                    'default_installment_id': self.fee_policy_line_id.id,
                }
            }
            
            
    def pay_student_fee_cm(self,student_fee_ids):
        """
        Central method that is called by wizard and cron job 
        Will set a meeting with client wahter needed a cron job for payment of student 
        fee or not, or it is already done by the payment wizard. may be we dont need cron job--shahid 27 june
        """
        for stdfee in student_fee_ids:
            fees =self.env['student.fee'].browse(stdfee['std_fee_id'])
            fees.write({'status':'paid','payment_date':stdfee['payment_date']})
            if fees.student_id:
                fees.student_id.message_post(body='Fee Paid for '+str(fees.student_id.full_name)+'.'+str(fees.name))
        return 
            
    
    def student_fee_reports_cm(self,date_from,date_to,student_ids=False,status=False):
        """
        This is Main central method that returns student fee details,
        Created by Sohail 23-June-2021
        
        Called by
        1) fee collection dues report
        """
        print("student ids...",student_ids)
        print("status...",status)
        std_result = self.env['student.fee'].search([('student_id', 'in', student_ids),('due_date', '>=', date_from),('due_date', '<=', date_to),('status', 'in', status)])
        mydict = {'total_amount': '','discount':'','net_amount':'','detail_dict':''}
        result = []
        result2 = []
        total_amt = 0
        total_disc = 0
        total_net_amt = 0
        for std in std_result:
            total_amt = total_amt + std.total_amount
            total_disc = total_disc + std.sibling_disc + std.emp_chil_disc + std.cash_discount
            total_net_amt = total_net_amt + std.applied_fee
            
            fee_records = {'std_name':'','fee_name':'','fee_date':'', 'due_date':'', 'total_amount':'', 'child_disc':'', 'cash_disc':'', 'applied_fee':'', 'payment_date':'', 'status':''}
            
            if std.student_id.state != 'Admitted':
                std_name = str(std.student_id.full_name)+"*"
            else:
                std_name = str(std.student_id.full_name)
                
            fee_records['std_name'] = std.student_id.full_name if std.student_id.full_name and len(std.student_id.full_name) > 0 else std.student_id.name
            fee_records['fee_name'] = std.name
            fee_records['fee_date'] = str(std.fee_date)
            fee_records['due_date'] = str(std.due_date)
            fee_records['total_amount'] = std.total_amount
            fee_records['child_disc'] = std.sibling_disc + std.emp_chil_disc + std.cash_discount #combined all 3 disocunts types
            fee_records['cash_disc'] = std.cash_discount
            fee_records['applied_fee'] = std.applied_fee
            fee_records['payment_date'] = std.payment_date
            fee_records['status'] = std.status
            
            result2.append(fee_records)
        mydict['total_amount'] = total_amt
        mydict['discount'] = total_disc
        mydict['net_amount'] = total_net_amt
        mydict['detail_dict'] = result2
        result.append(mydict)
        return result
    
    
    @api.depends('student_id.first_name_arabic', 'student_id.middle_name_arabic', 'student_id.second_middle_name_arabic', 'student_id.last_name_arabic')
    def _compute_student_name_arabic(self):
        for rec in self:
            rec.student_name_arabic = rec.student_id.full_name_arabic

    name = fields.Char(string = 'Fee',compute='compute_name')
    student_id = fields.Many2one('academic.student', string="Student", required=True)
    student_name_arabic = fields.Char(compute='_compute_student_name_arabic', string='Student Name Arabic', tracking=True, store=True)
    fee_type_id = fields.Many2one('fee.type', 'Fee Type', related="fee_policy_line_id.fee_type_id")
    fee_date = fields.Date('Fee Date', required=True, tracking=True)
    due_date = fields.Date('Due Date',  tracking=True)
    warning_date = fields.Date('Warning Date',tracking=True)
    total_amount = fields.Float(string = 'Fee',default=0.0, required=True, tracking=True)
    emp_chil_disc = fields.Float(string = 'Emp Child Dis',default=0.0,tracking=True)
    sibling_disc = fields.Float(string = 'Sibl Dis',default=0.0,tracking=True)
    cash_discount = fields.Float('Discount',tracking=True)
    applied_fee = fields.Float(string='Fee Applied', compute='get_final_applied_fee')
    account_id = fields.Many2one('account.move', 'Journal Entry')
    journal_id = fields.Many2one('account.journal', 'Journal')
    from_account = fields.Many2one('account.account', 'From Account')
    to_account = fields.Many2one('account.account', 'To Account')
    status = fields.Selection([('unpaid', 'Unpaid'),('paid', 'Paid'),('refunded','Refunded'),('cancelled', 'Cancelled')], string='Status',tracking=True, default='unpaid')
    payment_date = fields.Date('Payment Date',tracking=True)
    fee_policy_line_id = fields.Many2one('fee.policy.line', string="Fee Policy Line")
    is_overdue = fields.Boolean(string ='Overdue',compute='find_is_overdue', store=True)
    serial_number = fields.Char('Serial Number')
    account_id = fields.Many2one('account.move', 'Journal Entry')

    grade_id = fields.Many2one('school.class', string='Grade', store=True)
    admission_Date = fields.Date(string='Admission Date', store=True)
    siblings_ids = fields.Many2many('academic.student', 'stud_fee_sibling_rel', 'student_id', 'sibling_id', string='Siblings',store=True)
    parent_employee_ids = fields.Many2many('hr.employee', string='Parent Employee', store=True)
    mother_starting_date = fields.Date('Mother Starting Date')
    father_starting_date = fields.Date('Father Starting Date')

    @api.onchange('student_id')
    def onchange_parent_employee(self):
        for record in self:
            record.grade_id = record.student_id.class_id
            record.admission_Date = record.student_id.date_of_apply
            record.siblings_ids = record.student_id.siblings_ids
            record.parent_employee_ids = [(6, 0, [record.student_id.father_employee_id.id or False,
                                                  record.student_id.mother_employee_id.id or False])]
            record.mother_starting_date = record.student_id.mother_employee_id.starting_date
            record.father_starting_date = record.student_id.father_employee_id.starting_date


    @api.model_create_multi
    def create(self, vals_lst):
        """
        Overridden create() method to set the sequence on the student fee
        ------------------------------------------------------------------
        @param vals_lst: A list of dictionary containing fields and values
        @return: A newly created recordset.
        """
        sequ = self.env.ref('sms_core.sequence_student_fee')
        for vals in vals_lst:
            vals.update({
                'serial_number': sequ.next_by_id()
                })
            res = super(StudentFee, self).create(vals_lst)
            mail_ids = []
            mail_pool = self.env['mail.mail']
            if res.status == 'unpaid':
                values = {}
                values.update({'subject': 'Pending Instalments'})

                body_html = """<div>
                        <p>Dear Mr.""" + str(res.student_id.first_name) + ' ' + str(
                    res.student_id.middle_name) + ' ' + str(res.student_id.second_middle_name) + ' ' + str(
                    res.student_id.last_name) + """,
                        <br/>We kindly inform you that an amount of """ + str(
                    res.total_amount) + """ has to be paid for """ + str(
                    res.fee_policy_line_id.fee_type_id.name) + """ before """ + str(res.fee_policy_line_id.due_date) + """<br/></p>
                         </div>"""
                unpaid_records = self.search([('student_id', '=', res.student_id.id), ('status', '=', 'unpaid'),
                                              ('id', '!=', res.id)])
                if unpaid_records:
                    installment_list = '<br/> We would also like to kindly remind you of the other due amounts: <br/>'
                    installment_list_lines = ''
                    unpaid_records_total_amount = 0.0
                    for fee in unpaid_records:
                        installment_list_lines = installment_list_lines + str(fee.total_amount) + ' for ' + str(
                            fee.fee_type_id.name) + ' before ' + str(fee.due_date) + '<br/>'
                        unpaid_records_total_amount = unpaid_records_total_amount + fee.total_amount
                    body_html = body_html + installment_list + installment_list_lines
                    body_html = body_html + '<br/>Total amount: ' + str(unpaid_records_total_amount + res.total_amount)
                body_html = body_html + '<br/> Thank you for taking the time to look into this. We wish you a pleasant day.'
                if res.student_id.father_email:
                    mail_ids.append(res.student_id.father_email)
                if res.student_id.mother_email:
                    mail_ids.append(res.student_id.mother_email)
                if res.student_id.guardian_email:
                    mail_ids.append(res.student_id.guardian_email)
                values.update({'email_to': ','.join(mail_ids)})
                values.update({'body_html': body_html})
                values.update({'body': body_html})
                msg_id = mail_pool.create(values)
                if msg_id:
                    msg_id.send()

            elif res.status == 'paid':
                subject = 'Fee Payment'
                body_html = """<div>
                        <p>Dear Mr.""" + str(res.student_id.first_name) + ' ' + str(
                    res.student_id.middle_name) + ' ' + str(res.student_id.second_middle_name) + ' ' + str(
                    res.student_id.last_name) + """,<br/>
                        We kindly confirm that an amount of """ + str(
                    res.total_amount) + """ has been settled for """ + str(res.fee_type_id.name) + """ on """ + str(
                    res.payment_date) + """<br/></p>
                        </div>"""
                unpaid_records = self.search([('student_id', '=', res.student_id.id), ('status', '=', 'unpaid'),
                                              ('id', '!=', res.id)])
                if unpaid_records:
                    installment_list = '<br/> We would also like to kindly remind you of the other due amounts: <br/>'
                    installment_list_lines = ''
                    unpaid_records_total_amount = 0.0
                    for fee in unpaid_records:
                        installment_list_lines = installment_list_lines + str(fee.total_amount) + ' for ' + str(
                            fee.fee_type_id.name) + ' before ' + str(fee.due_date) + '<br/>'
                        unpaid_records_total_amount = unpaid_records_total_amount + fee.total_amount
                    body_html = body_html + installment_list + installment_list_lines
                    body_html = body_html + '<br/>Total amount: ' + str(unpaid_records_total_amount)
                body_html = body_html + '<br/> Thank you for taking the time to look into this. We wish you a pleasant day.'
                if res.student_id.father_email:
                    mail_ids.append(res.student_id.father_email)
                if res.student_id.mother_email:
                    mail_ids.append(res.student_id.mother_email)
                if res.student_id.guardian_email:
                    mail_ids.append(res.student_id.guardian_email)
                values = ({'email_to': ','.join(mail_ids), 'body_html': body_html, 'body': body_html,
                           'subject': subject})
                msg_id = mail_pool.create(values)
                if msg_id:
                    msg_id.send()

            elif res.status == 'refunded':
                subject = 'Fee Refund'
                body_html = """<div>
                        <p>Dear Mr.""" + str(res.student_id.first_name) + ' ' + str(
                    res.student_id.middle_name) + ' ' + str(res.student_id.second_middle_name) + ' ' + str(
                    res.student_id.last_name) + """,<br/>
                         We kindly confirm that an amount of """ + str(
                    res.total_amount) + """ has been refunded for """ + str(res.fee_type_id.name) + """ on """ + str(
                    res.payment_date) + """<br/>
                         If the payment was done through a credit card, then the refund shall take place within 10 working days</p>
                         </div>"""
                unpaid_records = self.search([('student_id', '=', res.student_id.id), ('status', '=', 'unpaid'),
                                              ('id', '!=', res.id)])
                if unpaid_records:
                    installment_list = '<br/> We would also like to kindly remind you of the other due amounts: <br/>'
                    installment_list_lines = ''
                    unpaid_records_total_amount = 0.0
                    for fee in unpaid_records:
                        installment_list_lines = installment_list_lines + str(fee.total_amount) + ' for ' + str(
                            fee.fee_type_id.name) + ' before ' + str(fee.due_date) + '<br/>'
                        unpaid_records_total_amount = unpaid_records_total_amount + fee.total_amount
                    body_html = body_html + installment_list + installment_list_lines
                    body_html = body_html + '<br/>Total amount: ' + str(unpaid_records_total_amount )
                body_html = body_html + '<br/> Thank you for taking the time to look into this. We wish you a pleasant day.'
                if res.student_id.father_email:
                    mail_ids.append(res.student_id.father_email)
                if res.student_id.mother_email:
                    mail_ids.append(res.student_id.mother_email)
                if res.student_id.guardian_email:
                    mail_ids.append(res.student_id.guardian_email)
                values = ({'email_to': ','.join(mail_ids), 'body_html': body_html, 'body': body_html,
                           'subject': subject})
                msg_id = mail_pool.create(values)
                if msg_id:
                    msg_id.send()
            return res

    def print_report(self):
        data = {
            'ids': self.ids,
            'model': 'student.fee'
        }
        return self.env.ref('sms_core.action_student_fee_report_pdf').report_action(self, data=data)

    def fee_payment(self):
        std_fee_ids = self.env['student.fee'].search([('id', '=', self.id), ('status', '=', 'unpaid')])
        wiz_lines = [(0, 0, {'student_id': std_fee_ids.student_id.id, 'std_fee_id': std_fee_ids.id, 'status': 'unpaid',
                             'payment_date': None, 'applied_fee': std_fee_ids.applied_fee,
                             'due_date': std_fee_ids.due_date, 'is_overdue': std_fee_ids.is_overdue})]
        wiz = self.env['student.fee.payment.wizard'].create(
            {'mode': 'pay_student_fee', 'operation_type': 'single_record', 'installment_id': self.fee_policy_line_id.id,
             'student_fee_ids': wiz_lines})

        if std_fee_ids:
            form_id = self.env.ref('sms_core.view_student_fee_payment_wizard', False)
            return {
                'name': 'Pay Student Fee',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'student.fee.payment.wizard',
                'view_id': form_id.id,
                'type': 'ir.actions.act_window',
                'target': 'new',
                'res_id': wiz.id,
                'context': {
                    'default_installment_id': self.fee_policy_line_id.id,
                }
            }