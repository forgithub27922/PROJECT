from datetime import datetime

from dateutil.relativedelta import relativedelta
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, Warning
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DTFORMAT
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as OE_DATEFORMAT
import math


class EmployeeLoan(models.Model):
    _name = 'hr.employee.loan'
    _inherit = ['mail.thread']
    _description = 'Employee Loan'
    _order = 'name desc'

    @api.constrains('loan_amount', 'installment_number')
    def _check_loan_amount(self):
        """
        Validation for loan amount and installment number should not be 0
        :return:
        """
        if self.loan_amount <= 0.0:
            raise ValidationError(_("Loan amount should be greater then 0"))
        if self.calculate_type == 'auto' and self.installment_number <= 0:
            raise ValidationError(
                _("Installment Number should be greater then 0"))

        if self.calculate_type == 'manual' and self.calculate_amount <= 0:
            raise ValidationError(
                _("Installment Amount should be greater then 0"))

    @api.model
    def _get_sequence(self):
        seq = self.env['ir.sequence'].with_context({'company_id':self.company_id.id}).next_by_code('hr.employee.loan')
        return seq

    def _get_current_date(self):
        return datetime.now().strftime(OE_DTFORMAT)

    @api.model
    def _get_employee_name(self):
        """
        for getting current logged in users' employee in loan form
        :return:
        """
        employee_rec = self.env['hr.employee'] \
            .search([('user_id', '=', self._uid)], limit=1)
        return employee_rec and employee_rec.id

    @api.depends('loan_installment_ids')
    def compute_installment_payment(self):
        """
        compute
        - total paid installment amount
        - remaining installments total_amount
        :return:
        """
        for rec in self:
            total_paid_installment = 0.00
            for inst_line in rec.loan_installment_ids:
                if inst_line.state == 'done':
                    total_paid_installment += inst_line.amount
            rec.total_paid_installment_amount = total_paid_installment
            rec.remaining_installments_total_amount = \
                rec.loan_amount - total_paid_installment

    name = fields. \
        Char(string="Request Number", copy=False)
    employee_id = fields.Many2one('hr.employee', 'Employee Name',
                                  default=_get_employee_name,
                                  copy=False)
    manager_id = fields.Many2one('hr.employee', string='Manager')
    department_id = fields.Many2one('hr.department', string='Department')
    designation_id = fields.Many2one('hr.job', string="Designation")
    account_analytic_id = fields.Many2one('account.analytic.account',
                                          string="Analytic Account")
    company_id = fields.Many2one(comodel_name='res.company',
                                 default=lambda self: self.env.user.company_id,
                                 string='Company',
                                 )
    currency_id = fields.Many2one('res.currency', string='Currency', store=True)
    loan_installment_policy = fields.Selection([
        ('deserved', 'Deserved'),
        ('desired', 'Desired')], string='Installment Policy')
    loan_amount = fields.Float('Loan Amount')
    installment_number = fields.Integer('Installments Count')
    remarks = fields.Char('Remarks')
    state = fields.Selection([('draft', 'To Submit'),
                              ('hr_approval', 'HR Approval'),
                              ('finance_processing', 'Finance Processing'),
                              ('approved', 'Confirm'),
                              ('rejected', 'Rejected'),
                              ('cancelled', 'Cancelled'),
                              ('done', 'Done')],
                             string='Status', readonly=True,
                             track_visibility='onchange',
                             help='When the Loan is created the status is '
                                  '\'Draft\'.\n Then the request will be '
                                  'forwarded to approval.',
                             default='draft')
    loan_installment_ids = fields.One2many('loan.installments', 'loan_id')
    repayment_method = fields.Selection([('payroll', 'Payroll'),
                                         ('cash_bank', 'Cash/Bank')],
                                        copy=False,
                                        string='RePayment Method')
    total_paid_installment_amount = fields.Float(
        compute='compute_installment_payment',
        string='Total Paid Installment Amount')
    remaining_installments_total_amount = fields.Float(
        compute='compute_installment_payment',
        string='Remaining Installments Total Amount')
    loan_journal_id = fields.Many2one('account.journal', string='Journal',
                                      copy=False)
    debit_account_id = fields.Many2one('account.account',
                                       string='Loan Payment Account',
                                       copy=False)
    credit_account_id = fields.Many2one('account.account',
                                        string='Loan Installment Account',
                                        copy=False)
    loan_issuing_date = fields.Date(string='Loan Issuing Date', copy=False)
    payment_date = fields.Date(string='Installment Start Date', copy=False)
    account_move_id = fields.Many2one('account.move', string='Journal Entry',
                                      copy=False)
    accounting_date = fields.Date(string='Accounting Date', copy=False)
    comments = fields.Text('Comments')
    reject_reason = fields.Text('Reject Reason')
    loan_approve_date = fields.Date(string='Approved Date')
    calculate_type = fields.Selection([('auto', 'Installment Number'),
                                         ('manual', 'Installment Amount')],
                                        copy=False, default='auto',
                                        string='Calculation Method')
    calculate_amount = fields.Float(string="Installment Amount")
    move_ids = fields.Many2many('account.move', 'account_move_employee_lon_rel', string='Journal Entry', copy=False)
    is_installment_paid = fields.Boolean(string="Installment Paid",compute='check_any_installment_paid',copy=False)
    batch_employee_loan_id = fields.Many2one('batch.employee.loan',string="Batch Employee Loan")
    move_name = fields.Char(string="Move name", copy=False)

    @api.multi
    @api.depends('loan_installment_ids')
    def check_any_installment_paid(self):
        for loan in self:
            if any(loan_statement.state == 'done' for loan_statement in loan.loan_installment_ids):
                loan.is_installment_paid = True

    @api.onchange('company_id')
    def onchange_company_id(self):
        self.currency_id = False
        if self.company_id:
            self.currency_id = self.company_id.currency_id

    @api.onchange('employee_id')
    def onchange_employee(self):
        self.department_id =  self.designation_id = self.manager_id = False
        if self.employee_id:
            sudo_emp = self.employee_id.sudo()
            if sudo_emp.department_id:
                self.department_id = sudo_emp.department_id.id
            if sudo_emp.job_id:
                self.designation_id = sudo_emp.job_id.id
            if sudo_emp.parent_id:
                self.manager_id = sudo_emp.parent_id.id

    @api.multi
    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise Warning(_('You cannot delete loan request.'))
            if rec.batch_employee_loan_id and not self._context.get('from_loan_batch'):
                raise Warning(_('You cannot delete loan request which created from batch loan.'))
        return super(EmployeeLoan, self).unlink()

    @api.multi
    def _get_related_window_action_id(self, data_pool):
        """
        getting related window action for making email link
        :param data_pool:
        :return:
        """
        window_action_id = False
        window_action_ref = \
            'bista_employee_loan.open_loan_request_for_hr_approval'
        if window_action_ref:
            addon_name = window_action_ref.split('.')[0]
            window_action_id = window_action_ref.split('.')[1]
            window_action_id = \
                data_pool.get_object_reference(addon_name,
                                               window_action_id)[1] or False
        return window_action_id

    @api.multi
    def send_email_notification(self, template_xml_ref, model, users_emails):
        """
        this method will send email with context values

        :param template_xml_ref:
        :param model:
        :return:
        """
        return True
        # Make Commented Code for Email Notification.

#         ctx = dict(self._context)
#         base_url = self.env['ir.config_parameter'].get_param(
#             'web.base.url')
#         data_pool = self.env['ir.model.data']
#         template_pool = self.env['mail.template']
#         template_id = data_pool.get_object_reference(
#             'bista_employee_loan', template_xml_ref)[1]
#         action_id = self._get_related_window_action_id(data_pool)
#         if action_id:
#             display_link = True
#         template_rec = template_pool.browse(template_id)
#         if template_rec:
#             ctx.update({
#                 'email_to': users_emails,
#                 'base_url': base_url,
#                 'display_link': display_link,
#                 'action_id': action_id,
#                 'model': model,
#             })
#             template_rec.with_context(ctx).send_mail(self.id,
#                                                      force_send=True)

    @api.multi
    def action_submit_for_loan_hr_approval(self):
        """
        method call from Button Submit for Hr Approval
        :return:
        """
        if self.batch_employee_loan_id and not self._context.get('from_loan_batch'):
            raise Warning(_("You can't Submit for HR Approval because it created from batch loan."))
        self.write({'state': 'hr_approval'})
        if not self.loan_issuing_date:
            self.loan_issuing_date =  self._get_current_date()

        
        group_rec = self.env.ref('bista_employee_loan.group_loan_hr_approval')
        users_emails = ''
        for grp_user in group_rec.users:
            emp = self.env['hr.employee'].sudo().search([('user_id', '=',
                                                   grp_user.id)])
            for empl in emp:
                if empl:
                    users_emails += str(empl.work_email) + ","
        self.send_email_notification('loan_request_send_hr',
                                     'hr.employee.loan', users_emails)

    @api.multi
    def action_submit_for_finance_loan_approval(self):
        """
       method call from Button Submit for Finance Approval
       :return:
       """
        if self.batch_employee_loan_id and not self._context.get('from_loan_batch'):
            raise Warning(_("You can't Submit for Finance Approval because it created from batch loan."))

        self.write({'state': 'finance_processing'})
        group_rec = self.env.ref('bista_employee_loan.group_loan_finance_approval')
        users_emails = ''
        for grp_user in group_rec.users:
            emp = self.env['hr.employee'].search(
                [('user_id', '=', grp_user.id)])
            for empl in emp:
                if empl:
                    users_emails += str(empl.work_email) + ","
                    self.send_email_notification('loan_request_send_finance',
                                             'hr.employee.loan', users_emails)

    @api.multi
    def check_installments(self):
        if not self.loan_installment_ids:
            raise Warning(_('Kindly, click on calculate button to have a '
                            'full picture on your amortization schedule.'))

    @api.multi
    def action_approved_loan(self):
        """
       method call from Button Submit for Approve
       :return:
       """
        if self.batch_employee_loan_id and not self._context.get('from_loan_batch'):
            raise Warning(_("You can't Approved Loan because it created from batch loan."))

        self.check_installments()
        self.write({'state': 'approved',
                    'name': self._get_sequence(),
                    'loan_approve_date': self._get_current_date()})
        self.send_email_notification('loan_request_send_approved',
                                     'hr.employee.loan', False)
        message = ('''<ul class="o_mail_thread_message_tracking">
                      <li>Loan Approve Date Date: %s</li>
                      <li>Loan Number: %s </li>
                      <li>State: %s</li>
                      </ul>''') % (
            datetime.now().strftime(OE_DTFORMAT),
            self.name, self.state.title())
        self.accounting_date = self._get_current_date()
        self.message_post(body=message)
        if not self.batch_employee_loan_id:
            self.action_move_create()

    @api.multi
    def action_submit_loan_reject(self):
        """
        this method will call for reject loan request
        this will open wizard for reject reason
        :return:
        """
        if self.batch_employee_loan_id:
            raise Warning(_("You can't Reject Loan because it created from batch loan."))

        ctx = dict(self._context)
        form_view = self.env.ref(
            'bista_employee_loan.hr_employee_loan_reject_form_view')
        return {
            'name': _('Reject Reason'),
            'res_model': 'loan.reject.reason',
            'views': [(form_view.id, 'form'), ],
            'type': 'ir.actions.act_window',
            'context': ctx,
            'target': 'new'
        }

    @api.multi
    def action_submit_loan_cancelled(self):
        """
        This method will call when user press cancel loan request and loan
        request will be in cancelled state
        """
        if any(loan_installment.state == 'done' for loan_installment in self.loan_installment_ids):
            raise ValidationError(_("You can't cancel the Loan because installment are paid.!"))

        if self.batch_employee_loan_id and not self._context.get('from_loan_batch'):
            raise Warning(_("You can't Cancel Loan because it created from batch loan."))

        # for account_move in self.move_ids:
        self.account_move_id.button_cancel()
        self.account_move_id.with_context({'custom_move':True}).unlink()
        self.write({'state': 'cancelled'})
        self.loan_installment_ids.write({'state': 'cancel'})

    @api.multi
    def action_loan_reset_to_draft(self):
        for loan in self:
            if loan.batch_employee_loan_id and not self._context.get('from_loan_batch'):
                raise Warning(_("You can't Reset to Draft because it created from batch loan."))
            loan.state ='draft'
            loan.loan_installment_ids.write({'state': 'draft'})

    @api.multi
    def calculate_loan_amount(self):
        """
          method call from Button Calculate Loan Insallments
          :return:
          """
        loan_list = []
        if not self.installment_number:
            raise Warning(_('Kindly, enter an installment count for '
                            'calculating installments.'))

        for rec in self:
            loan_amount = rec.loan_amount
            installment_number = rec.installment_number
            if loan_amount and installment_number:
                amount = loan_amount / installment_number
                total_amount = 0.0
                payroll_run_date = datetime.strptime(self.payment_date,
                                                     OE_DATEFORMAT)
                du_date = 0
                # create installment
                for duration in range(1, installment_number + 1):
                    vals = {
                        'due_date': payroll_run_date + relativedelta(
                            months=du_date),
                        'amount': round(amount, 2),
                        'state': 'draft',
                        'loan_id': rec.id
                    }
                    loan_list.append((0, 0, vals))
                    # loan_installment_obj.create(vals)
                    total_amount += round(amount, 2)
                    du_date = duration
                last_amount = loan_amount - total_amount
                # last installment adding for solve rounding issues
                if last_amount != 0:
                    loan_list[-1][2]['amount'] = \
                        loan_list[-1][2].get('amount') + last_amount
                # To remove duplicate lines
            for installment_rec in self.loan_installment_ids:
                loan_list.append((2, installment_rec.id))

            self.loan_installment_ids = loan_list

    @api.multi
    def calculate_installment_amount(self):
        """
          method call from Button Calculate Loan Insallments with user input.
          i.e Loan Amount is 1750 and user give amount as 500
          then Installments will be as following,
          Installment 1-500, Installment 2-500,
          Installment 3-500, Installment 4-250.
          :return:
          """
        loan_list = []
        if not self.calculate_amount:
            raise Warning(_('Kindly, enter an installment Amount for '
                            'calculating installments.'))

        for rec in self:
            loan_amount = rec.loan_amount
            ins_num = math.ceil(loan_amount / self.calculate_amount)
            installment_number = ins_num
            if loan_amount and installment_number:
                amount = self.calculate_amount
                total_amount = 0.0
                payroll_run_date = datetime.strptime(self.payment_date,
                                                     OE_DATEFORMAT)
                du_date = 0
                last_amount = 0.0
                # create installment
                for duration in range(1, installment_number + 1):
                    vals = {
                        'due_date': payroll_run_date + relativedelta(
                            months=du_date),
                        'amount': round(amount, 2),
                        'state': 'draft',
                        'loan_id': rec.id
                    }
                    if last_amount < amount and last_amount != 0.0:
                        vals['amount'] = round(last_amount, 2)
                    else:
                        vals['amount'] = round(amount, 2)
                    loan_list.append((0, 0, vals))
                    # loan_installment_obj.create(vals)
                    total_amount += round(amount, 2)
                    du_date = duration
                    last_amount = loan_amount - total_amount
                    # To remove duplicate lines
            for installment_rec in self.loan_installment_ids:
                loan_list.append((2, installment_rec.id))

            self.loan_installment_ids = loan_list

    @api.multi
    def clear_installment_line(self):
        """
        this method will clear loan installments
        :return:
        """
        self.write(
            {'loan_installment_ids': [(2, self.loan_installment_ids.ids)]})

    @api.multi
    def action_move_create(self):
        '''
        :return: Create First entry of total loan amount.
        '''
        move = self.env['account.move'].create({
            'journal_id':self.loan_journal_id.id,
            'company_id':self.company_id.id,
            'date': self.accounting_date,
            'ref': self.name + self.employee_id.name,
            'name': self.name
        })
        if move:
            move_line_lst = self._prepare_move_lines(move)
            move.line_ids = move_line_lst
            move.post()
            move.button_cancel()
            self.write({'account_move_id': move.id,
                        'move_name':move.name,
                        'move_ids':[(4, move.id)]})

    def _prepare_move_lines(self, move):
        '''
        :param move: Created move.
        :return: Create Approve loan JE's(First JE's).
        '''
        move_lst = []
        if self.loan_journal_id and \
            (not self.loan_journal_id.default_debit_account_id
             or not self.loan_journal_id.default_credit_account_id):
            raise Warning(_('Selected journal have must be Default Credit and '
                            'Debit account.'))

        partner = self.employee_id.partner_id.id if self.employee_id.partner_id else False
        generic_dict = {
            'name': self.name,
            'company_id':self.company_id.id,
            'currency_id':self.company_id.currency_id.id,
            'date_maturity': self.loan_issuing_date,
            'journal_id':self.loan_journal_id.id,
            'date': self.accounting_date,
            'partner_id': partner,
            'quantity': 1,
            'move_id': move.id,
        }
        debit_entry_dict = {
            'account_id': self.credit_account_id.id,
#             'account_id': self.loan_journal_id.default_credit_account_id.id,
            'debit': self.loan_amount,
        }
        credit_entry_dict = {
#             'account_id': self.debit_account_id.id,
            'account_id':
#                 self.loan_journal_id and
#                 self.loan_journal_id.default_credit_account_id and
                self.debit_account_id.id,
            'credit': self.loan_amount,
        }
        debit_entry_dict.update(generic_dict)
        credit_entry_dict.update(generic_dict)
        move_lst.append((0, 0, debit_entry_dict))
        move_lst.append((0, 0, credit_entry_dict))
        return move_lst

    @api.multi
    def action_open_journal_entries(self):
        res = self.env['ir.actions.act_window'].\
            for_xml_id('account', 'action_move_journal_line')
        # DO NOT FORWARD-PORT
        res['domain'] = [('id', 'in', self.move_ids.ids)]
        res['context'] = {}
        return res

    @api.multi
    def action_to_pay_loan(self):
        '''
        :return: Loan payment.
        '''
        self.ensure_one()
        context = dict(self._context)
        if self.state != 'approved':
            raise ValidationError(_('Loan state must be Confirmed!!!'))
        select_loan_installment_lines = self.loan_installment_ids.filtered(lambda l:l.select_loan and l.state in ['draft', 'lock'])
        if not select_loan_installment_lines:
            raise Warning(_('Please select Loan Installment lines for early payment.'))
        total_amount = sum(select_loan_installment_lines.mapped('amount'))
#         self.amount = total_amount 
#         remain_amount = sum(installment.amount for installment in
#                             self.loan_installment_ids.filtered(
#                                 lambda x: x.state not in
#                                           ('cancel', 'reject', 'done')))
        partner = (self.employee_id.user_id and \
                  self.employee_id.user_id.partner_id.id) or False
        module = self.env['ir.module.module'].sudo().search([
            ('name', '=', 'bista_hr_gratuity')])
        if module and not partner:
            partner = self.employee_id.partner_id and \
                      self.employee_id.partner_id.id or False
        if not partner:
            raise ValidationError(_('Employee have no partner!'))

        form_view = self.env.ref(
            'bista_employee_loan.loan_register_payment_view_form')

        loan_account = self.loan_journal_id.default_debit_account_id and \
                       self.loan_journal_id.default_debit_account_id.id or \
                       False,
#         loan_account = self.credit_account_id.id
        if not loan_account:
            raise ValidationError(_('Selected loan journal have no debit '
                                    'account!'))
        context.update({'default_amount': total_amount,
                        'loan_account_id': loan_account})
        return {
            'name': _('Pay Loan'),
            'type': 'ir.actions.act_window',
            'view_id': form_view.id,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'loan.register.payment.wizard',
            'target': 'new',
            'context': context,
        }


class LoanInstallments(models.Model):
    _name = 'loan.installments'
    _description = 'Loan Installment'
    _inherit = ['mail.thread']
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee',
                                  related='loan_id.employee_id',
                                  string='Employee', store=True)
    due_date = fields.Date(string='Due Date')
    amount = fields.Float('Amount')
    remarks = fields.Text(string='Remarks')
    loan_id = fields.Many2one('hr.employee.loan', string='Loan Request')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('reject', 'Reject'),
        ('lock', 'Rescheduled'), ('cancel', 'Cancelled'), ('done', 'Done')],
        string='State',
        default='draft', track_visibility='onchange')
    paid_amount = fields.Float(string='Total Paid Amount')
    paid_date = fields.Date(string='Paid Date', track_visibility='onchange')
    residual_amount = fields.Float(string='Residual Amount')
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)
    prev_due_date = fields.Date(string='Previous Date')
    select_loan = fields.Boolean(string="Select Installment")

    @api.multi
    def button_reschedule(self):
        """
        this method will reschedule installments
        :return:
        """

        if self.loan_id:
            self.write({'state': 'lock'})

    @api.multi
    def button_reject(self):
        """
        this method will reject reschedule req and 
        apply due date which was previously due date
        :return: 
        """
        if self.prev_due_date:
            self.due_date = self.prev_due_date
            self.state = 'reject'

    @api.multi
    def ask_for_reschedule(self):
        """
        this method will move record in asked for reschedule
        :return: False
        """
        if self.loan_id.state == 'approved':
            ctx = dict(self._context)
            ctx.update({'loan_installment': self.id})
            form_view = self.env.ref('bista_employee_loan.loan_reschedule_installment')

            return {
                'name': _('Reschedule'),
                'res_model': 'reschedule.installment.wizard',
                'views': [(form_view.id, 'form'), ],
                'type': 'ir.actions.act_window',
                'context': ctx,
                'target': 'new'
            }
            # self.write({'state': 'lock'})
        else:
            raise Warning(_('You cannot reschedule untill loan approved.'))
        
