from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
from odoo.tools import float_compare, float_is_zero
from datetime import time as datetime_time
from dateutil import rrule


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    email_sended = fields.Boolean(string='Notification Sended', default=False)
    is_paid = fields.Boolean('Is Paid', help="For hide Pay button.")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('verify', 'Waiting'),
        ('done', 'Done'),
        ('paid', 'Paid'),
        ('cancel', 'Rejected')],
        string='Status', index=True, readonly=True, copy=False, default='draft',
        help="""* When the payslip is created the status is \'Draft\'
                    \n* If the payslip is under verification, the status is \'Waiting\'.
                    \n* If the payslip is confirmed then status is set to \'Done\'.
                    \n* If the payslip is pay then status is set to \'Paid\'.
                    \n* When user cancel payslip the status is \'Rejected\'.""")
    account_move_id = fields.Many2one('account.move',
                                      string='Payment Matching', copy=False)
    no_of_days = fields.Float('Number of days')  
    move_name = fields.Char(string="Move Name", copy=False)
    calculate_total_days = fields.Float(string="Total Days", compute='_calculate_total_days', store=True)
    employee_payment_journal_id = fields.Many2one('account.journal', string="Payment Journal")

    @api.depends('worked_days_line_ids')
    def _calculate_total_days(self):
        for payslip in self:
            payslip.calculate_total_days = sum(payslip.worked_days_line_ids.mapped('number_of_days'))

    @api.model
    def get_worked_day_lines(self, contracts, date_from, date_to):
        """
        @param contract: Browse record of contracts
        @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
        """
        res = []
        # fill only if the contract as a working schedule linked
        for contract in contracts.filtered(
                lambda contract: contract.resource_calendar_id):
            day_from = datetime.combine(fields.Date.from_string(date_from),
                                        datetime_time.min)
            day_to = datetime.combine(fields.Date.from_string(date_to),
                                      datetime_time.max)
 
            # compute leave days
            leaves = {}
            hr_holiday_obj = self.env['hr.holidays']
            hr_holiday_obj = self.get_hr_leave_date_range(day_from, date_to, contract.employee_id)
            for holiday in hr_holiday_obj:
                leaves.setdefault(
                        holiday.holiday_status_id, {
                            'name': holiday.holiday_status_id.name,
                            'sequence': 5,
                            'code': holiday.holiday_status_id.code or holiday.holiday_status_id.name,
                            'number_of_days':0.00,
                            'number_of_hours': 0.0,
                            'contract_id': contract.id,
                        })

            diff_days = (day_to - day_from).days + 1
            holiday_leave_count = 0.00
            for holiday in hr_holiday_obj:
                for key, value in leaves.items():
                    if holiday.holiday_status_id == key:
                        leave_count = self.get_leave_count(day_from, day_to, holiday)
                        value['number_of_days'] += leave_count
                        holiday_leave_count += leave_count
                        value['number_of_hours'] += (value['number_of_days'] * 7)

            # compute worked days
            working_days = diff_days - holiday_leave_count
            attendances = {
                'name': _("Normal Working Days paid at 100%"),
                'sequence': 1,
                'code': 'WORK100',
                'number_of_days': working_days,
                'number_of_hours': working_days * 7,
                'contract_id': contract.id,
            }

            res.append(attendances)
            res.extend(leaves.values())
        return res

    def get_hr_leave_date_range(self, day_from, day_to, employee_id):
        domain = [
                ('date_from', '<=', day_to),
                ('date_to', '>=', day_from),
                ('employee_id', '=', employee_id.id),
                ('type', '=', 'remove'),
                ('lapse_leave','=',False),
                ('state', '=', 'validate'),
            ]
        return self.env['hr.holidays'].search(domain)

    def get_leave_count(self, day_from, day_to, holiday):
        count = 0
        date_from = datetime.strptime(holiday.date_from, '%Y-%m-%d').date()
        date_to = datetime.strptime(holiday.date_to, '%Y-%m-%d').date()
        for day in rrule.rrule(rrule.DAILY,
                               dtstart=day_from.date(),
                               until=day_to.date()):
            day = day.date()
            if day >= date_from and day <= date_to:
                count += 1
        return count

    @api.model
    def create(self, vals):
        if vals.get('payslip_run_id', False):
            run_rec = self.env['hr.payslip.run'].browse(
                vals.get('payslip_run_id'))
            if run_rec and run_rec.journal_id:
                vals.update({
                    'journal_id': run_rec.journal_id.id})
        res = super(HrPayslip, self).create(vals)
        return res

    @api.onchange('date_to', 'date_from')
    def onchange_date(self):
        if self.date_from and self.date_to:
            d1 = datetime.strptime(self.date_from, "%Y-%m-%d")
            d2 = datetime.strptime(self.date_to, "%Y-%m-%d")
            self.no_of_days = abs((d2 - d1).days)

    @api.multi
    def action_payslip_done(self):
        print("\n\n\n PAYSLIP DONE ::::::::::::::::::--------------------------------->")
        """Update partner id in JE/JI when payslip confirm."""
        if self.payslip_run_id:
            raise UserError(_("Please Confirm payslip from batch '%s'.") % (self.payslip_run_id.name))

        if self.contract_id.state != 'open':
            raise UserError(_('Make sure Contract in Running state for employee %s.' % (self.employee_id.display_name)))

        if not self.contract_id.analytic_account_id:
            raise UserError(_('cost centre is missing on the employee %s contract.' % (self.employee_id.display_name)))

        ctx = self._context.copy()
        if self.company_id and self.company_id.send_payslip:
            template = self.env.ref('bista_payroll.payslip_send_email',
                                    raise_if_not_found=False)
            if not template:
                raise UserError(
                    _('The Payslip Email Template is not in the database'))
            self.send_payslip_email(template)
        
        if self.move_name:
            ctx.update({'payslip_id':self})
            res = super(HrPayslip, self.with_context(ctx)).action_payslip_done()
        else:
            res = super(HrPayslip, self).action_payslip_done()
        self.move_name = self.move_id.name
#         for mov_line in self.move_id.line_ids:
#             if mov_line.credit == self.net_amount:
#                 mov_line.partner_id = self.employee_id.partner_id.id or False
        for payslip in self:
            move_id = payslip.move_id
            move_id.line_ids.remove_move_reconcile()
            move_id.button_cancel()
        return res

    @api.multi
    def action_view_entries(self):
        '''
        :return: View `journal entries.
        '''
        self.ensure_one()
        form_view = self.env.ref('account.view_move_form', False)
        return {
            'name': _('Journal Entries'),
            'res_model': 'account.move',
            'res_id': self.account_move_id.id,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'context': self._context,
        }

    @api.multi
    def send_payslip_email(self, template):
        """
        send email generic method for send email
        :param template: template rec
        :return:
        """
        if not template:
            raise UserError(
                _('The Payslip Email Template is not in the database'))
        template.send_mail(self.id, force_send=True)
        self.email_sended = True

    @api.multi
    def action_payslip_send(self):
        '''
        This function opens a window to compose an email,
        with the edi payslip template message loaded by default
        '''

        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = \
            ir_model_data.get_object_reference('bista_payroll', 'payslip_send_email')[
                1]
        except ValueError:
            template_id = False
        try:
            print("under 2nd try !!!!!!!!!!---------------------------------------->")
            compose_form_id = \
                ir_model_data.get_object_reference('mail',
                                                   'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = {
            'default_model': 'hr.payslip',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'custom_layout': "mail_template_data_notification_email_payslip",
            'proforma': self.env.context.get('proforma', False),
            'force_email': True,
            'email_to': self.employee_id.work_email
        }
        print("\n\n CTX !!!!!!!!!!!!!!!!!!!!!!!!!---------------------------------->", ctx)
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def action_to_pay(self):
        self.ensure_one()
        ctx = dict(self._context)
        if self.payslip_run_id:
            raise UserError(_("Please make payment from batch payslip '%s'.") % (self.payslip_run_id.name))

        if self.state == 'paid':
            raise UserError(_("Payslips has been already paid!"))
        if self.state != 'done':
            raise UserError(_("All the payslips must be Done!"))

        journal_id = self.employee_id.journal_id.sudo()
        if not journal_id:
            raise UserError(_("employee have not set Payment Mode!"))

        payment_line_lst = []
        payment_line_lst.append((0, 0, {'journal_id': journal_id.id, 'amount':self.net_amount}))

        ctx.update({'default_payment_line_ids':payment_line_lst})

        form_view = self.env.ref('bista_payroll.view_hr_payslip_payment_form')
        return {
            'name': 'Pay to Payslip',
            'type': 'ir.actions.act_window',
            'view_id': form_view.id,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hr.payslip.payment',
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def action_set_to_draft(self):
        for slip in self:
            if slip.payslip_run_id and not self._context.get('from_batch_payslip'):
                raise UserError(_("You cannot Reset Payslip which are created from batch '%s'.") % (slip.payslip_run_id.name))

            if not self.env['ir.module.module'].sudo().search([('name', '=', 'account_cancel'), ('state', '=', 'installed')]):
                raise UserError(_("Needs To Install \'Account Cancel\' Module"))
            if slip.move_id:
                if slip.move_id.state == 'posted':
                    raise UserError(_("You can't cancel payslip because Journal Entry already posted.!"))
                if slip.move_id.journal_id.update_posted:
                    slip.move_id.button_cancel()
                    slip.move_id.with_context({'custom_move':True}).unlink()
                    slip.write({'state': 'draft'})
                else:
                    raise UserError(_(
                        "Goto Journal -> Adcanced Settings -> "
                        "Allow Cancelling Entries=True "))
        return True

    @api.multi
    def action_payslip_cancel(self):
        if self.filtered(lambda slip: slip.state == 'done'):
            raise UserError(_("Cannot cancel a payslip that is done."))
        if self.payslip_run_id:
            raise UserError(_("You cannot Cancel Payslip which are created from batch '%s'.") % (self.payslip_run_id.name))
        return self.write({'state': 'cancel'})


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    send_payslip = fields.Boolean(string="Send Payslip",
                                  related='company_id.send_payslip')
    hide_payslip_zero = fields.Boolean(string="Hide Payslip Lines",
                                       related='company_id.hide_payslip_zero')


class ResCompany(models.Model):
    _inherit = 'res.company'

    send_payslip = fields.Boolean()
    hide_payslip_zero = fields.Boolean()


class HrPayslipRun(models.Model):
    _name = 'hr.payslip.run'
    _inherit = ['hr.payslip.run','mail.thread', 'mail.activity.mixin']

    account_move_id = fields.Many2one('account.move',
                                      string='Payment Matching', copy=False)
    account_move_ids = fields.One2many('account.move', 'payslip_run_id',
                                       string='Journal Entry', copy=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('close', 'Close'),
        ('paid', 'Paid'),

    ], string='Status', index=True, readonly=True, copy=False, default='draft',track_visibility='onchange')
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)
    move_name = fields.Char(string="Move Name",copy=False)

    @api.multi
    def compute_payslip(self):
        if not self.slip_ids:
            raise UserError(
                _('No record found to Compute!'))
        for payslip in self.slip_ids:
            if payslip.contract_id.state != 'open':
                raise UserError(_('Make sure Contract in Running state for employee %s' % (payslip.employee_id.name)))
            payslip.onchange_date()
            payslip.with_context({'from_batch':True}).compute_sheet()

    @api.multi
    def confirm_payslip(self):
        if not self.slip_ids:
            raise UserError(
                _('No record found to confirm!'))
        payslip_rec = self.env['hr.payslip']
        payslip_rec_without_consolidate = self.env['hr.payslip']

        for payslip in self.slip_ids:
            if self.journal_id.id != payslip.journal_id.id:
                payslip.journal_id = self.journal_id.id

            if payslip.contract_id.state != 'open':
                raise UserError(_('Make sure Contract in Running state for employee %s.' % (payslip.employee_id.display_name)))

            # if not payslip.contract_id.analytic_account_id:
            #     raise UserError(_('cost centre is missing on the employee %s contract.' % (payslip.employee_id.display_name)))

            if payslip.company_id.consolidate_batch_payslip:
                payslip_rec += payslip
            else:
                payslip_rec_without_consolidate += payslip
        self.action_batch_payslip_done(payslip_rec_without_consolidate)
        self.action_cnslidt_batch_payslip_done(payslip_rec)
        move_ids = []
        for payslip in self.slip_ids:
            move_ids.append(payslip.move_id.id)
        self.write({'account_move_ids':[(6, 0, list(set(move_ids)))]})
        self.state = 'confirm'

    @api.multi
    def action_cnslidt_batch_payslip_done(self, payslip_rec):
        """
        creates batch journal for batch pay slip while confirm payslip
        :param payslip_rec: recordset of hr_payslip for which company
         contains consolidate_batch_payslip = true
        :return:
        """
        if payslip_rec:
            date = datetime.now()
            main_lst = []
            payslip_total_amount = 0.00
            debit_move_lines = {}
            analytic_debit_move_lines = {}
            credit_moves_line = {}
            analytic_credit_moves_line = {}
            header_credit_moves_line = {}
            narration = []
            debit_acc_lst = []

            for payslip in payslip_rec:
                date = payslip.date or payslip.date_to
                analytic_account_id = payslip.employee_id.contract_id.analytic_account_id.id

                payslip_total_amount += payslip.net_amount
                name = _('Payslip of %s') % (payslip.employee_id.name)
                narration.append(name)

                for line in payslip.details_by_salary_rule_category:
                    amount = payslip.credit_note and -line.total or line.total
                    if amount == 0.00:
                        continue
                    debit_account_id = line.salary_rule_id.account_debit.id
                    credit_account_id = line.salary_rule_id.account_credit.id
                    if not debit_account_id and line.code not in ['GROSS', 'NET']:
                        raise UserError (_("Configure Debit Account for %s Rule.") % (line.name))

                    if analytic_account_id:
                        analytic_debit_move_lines.setdefault(analytic_account_id, {})
                        if debit_account_id and not (amount < 0.0 and -amount):
                            if debit_account_id not in analytic_debit_move_lines[analytic_account_id]:
                                analytic_debit_move_lines[analytic_account_id].update({debit_account_id:self.get_debit_move_line(
                                                        debit_account_id, line, payslip, date, amount, analytic_account_id)})
                            else:
                                analytic_debit_move_lines[analytic_account_id][debit_account_id]['debit'] += amount > 0.0 and amount or 0.0
                                analytic_debit_move_lines[analytic_account_id][debit_account_id]['credit'] += amount < 0.0 and -amount or 0.0

                                label_name = line.salary_rule_id.report_header_id.name if line.salary_rule_id.report_header_id else line.name
                                if label_name.lower() not in analytic_debit_move_lines[analytic_account_id][debit_account_id]['name'].lower():
                                    analytic_debit_move_lines[analytic_account_id][debit_account_id]['name'] += ', ' + label_name

                        elif debit_account_id:
                            header_credit_moves_line.setdefault(analytic_account_id, {})
                            # Report Header Wise Group By
                            if line.salary_rule_id.report_header_id:
                                if debit_account_id not in header_credit_moves_line[analytic_account_id]:
                                    header_credit_moves_line[analytic_account_id].update({debit_account_id:{}})

                                if line.salary_rule_id.report_header_id.id not in header_credit_moves_line[analytic_account_id][debit_account_id]:
                                    header_credit_moves_line[analytic_account_id][debit_account_id].update({line.salary_rule_id.report_header_id.id:self.get_credit_move_line(
                                                debit_account_id, line, amount, payslip, date, analytic_account_id, line.salary_rule_id.report_header_id.name)})
                                else:
                                    header_credit_moves_line[analytic_account_id][debit_account_id][line.salary_rule_id.report_header_id.id]['credit'] += amount < 0.0 and -amount or 0.0

                            else:
                                analytic_credit_moves_line.setdefault(analytic_account_id, {})

                                if debit_account_id not in analytic_credit_moves_line[analytic_account_id]:
                                    analytic_credit_moves_line[analytic_account_id].update({debit_account_id:self.get_credit_move_line(
                                                debit_account_id, line, amount, payslip, date, analytic_account_id)})

                                else:
                                    analytic_credit_moves_line[analytic_account_id][debit_account_id]['credit'] += amount < 0.0 and -amount or 0.0
# 
#                                 credit_moves_line.setdefault(debit_account_id, self.get_credit_move_line(
#                                                 debit_account_id, line, 0.00, payslip, date, analytic_account_id))
#                                 credit_moves_line[debit_account_id]['credit'] += amount < 0.0 and -amount or 0.0

                                label_name = line.salary_rule_id.report_header_id.name if line.salary_rule_id.report_header_id else line.name
                                if label_name.lower() not in analytic_credit_moves_line[analytic_account_id][debit_account_id]['name'].lower():
                                    analytic_credit_moves_line[analytic_account_id][debit_account_id]['name'] += ', ' + label_name

                            if credit_account_id and amount != 0.0:
                                if credit_account_id not in credit_moves_line:
                                    credit_moves_line.update({credit_account_id:self.get_credit_move_line(
                                                           credit_account_id, line, amount, payslip, date, analytic_account_id)})
                                else:
                                    credit_moves_line[credit_account_id]['credit'] += amount < 0.0 and -amount or 0.0

                        if debit_account_id:
                            debit_acc_lst.append(debit_account_id)

                    else:
                        if debit_account_id and not (amount < 0.0 and -amount):
                            if debit_account_id not in debit_move_lines:
                                debit_move_lines.update({debit_account_id:self.get_debit_move_line(
                                                        debit_account_id, line, payslip, date, amount, analytic_account_id)})
                            else:
                                debit_move_lines[debit_account_id]['debit'] += amount > 0.0 and amount or 0.0
                                debit_move_lines[debit_account_id]['credit'] += amount < 0.0 and -amount or 0.0

                                label_name = line.salary_rule_id.report_header_id.name if line.salary_rule_id.report_header_id else line.name
                                if label_name.lower() not in debit_move_lines[debit_account_id]['name'].lower():
                                    debit_move_lines[debit_account_id]['name'] += ', ' + label_name
 
                        elif debit_account_id:
                            # Report Header Wise Group By
                            if line.salary_rule_id.report_header_id:
                                header_credit_moves_line.setdefault(debit_account_id, {})
                                if line.salary_rule_id.report_header_id.id not in header_credit_moves_line[debit_account_id]:
                                    header_credit_moves_line[debit_account_id].update({line.salary_rule_id.report_header_id.id:self.get_credit_move_line(
                                                debit_account_id, line, amount, payslip, date, analytic_account_id, line.salary_rule_id.report_header_id.name)})
                                else:
                                    header_credit_moves_line[debit_account_id][line.salary_rule_id.report_header_id.id]['credit'] += amount < 0.0 and -amount or 0.0

                            else:
                                credit_moves_line.setdefault(debit_account_id, self.get_credit_move_line(
                                                debit_account_id, line, 0.00, payslip, date, analytic_account_id))
                                credit_moves_line[debit_account_id]['credit'] += amount < 0.0 and -amount or 0.0

                                label_name = line.salary_rule_id.report_header_id.name if line.salary_rule_id.report_header_id else line.name
                                if label_name.lower() not in credit_moves_line[debit_account_id]['name'].lower():
                                    credit_moves_line[debit_account_id]['name'] += ', ' + label_name

                            if credit_account_id and amount != 0.0:
                                if credit_account_id not in credit_moves_line:
                                    credit_moves_line.update({credit_account_id:self.get_credit_move_line(
                                                           credit_account_id, line, amount, payslip, date, analytic_account_id)})
                                else:
                                    credit_moves_line[credit_account_id]['credit'] += amount < 0.0 and -amount or 0.0

#             for key, value in emp_salary_move_line_dict.items():
#                  main_lst += [(0, 0, self.get_adjustment_credit_move_line(date, value, key))]

            main_lst += [(0, 0, self.get_adjustment_credit_move_line(date, payslip_total_amount))]

            for account in list(set(debit_acc_lst)):
                for key, value in analytic_debit_move_lines.items():
                    if value.get(account):
                        if value.get(account)['debit'] == 0 and value.get(account)['credit'] == 0:
                            continue
                        main_lst += [(0, 0, value[account])]

            for key, value in debit_move_lines.items():
                if value['debit'] == 0 and value['credit'] == 0:
                    continue
                main_lst += [(0, 0, value)]

            for key, value in credit_moves_line.items():
                if value.get('debit') == 0 and value.get('credit') == 0:
                    continue
                main_lst += [(0, 0, value)]

            for account in list(set(debit_acc_lst)):
                for key, value in analytic_credit_moves_line.items():
                    if value.get(account):
                        if value.get(account)['debit'] == 0 and value.get(account)['credit'] == 0:
                            continue
                        main_lst += [(0, 0, value[account])]

            for account in list(set(debit_acc_lst)):
                for key, value in header_credit_moves_line.items():
                    if value.get(account):
                        for k, header_valule in value.get(account).items():
                            if header_valule.get('debit') == 0 and header_valule.get('credit') == 0:
                                continue
                            main_lst += [(0, 0, header_valule)]

            vals = {
            'journal_id': self.journal_id.id,
            'date': date,
            'line_ids': main_lst,
            'ref': self.name,
            'company_id':self.company_id.id,
            'narration':', '.join(x for x in narration)
            }
            if self.move_name:
                vals['name'] = self.move_name
            move_id = self.env['account.move'].sudo().create(vals)
            move_id.post()
            self.move_name = move_id.name
            move_id.button_cancel()
            for payslip in payslip_rec:
                payslip.write({'move_id': move_id.id, 'date': date, 'state': 'done'})

    @api.multi
    def action_batch_payslip_done(self, payslip_rec):
        old_move = self.env['account.move']
        if payslip_rec:
            precision = self.env['decimal.precision'].precision_get('Payroll')
            line_ids = []
            emp_name = []
            slip_number = []
            date = self.date_start
            for payslip in payslip_rec:
                if payslip.move_id:
                    old_move = payslip.move_id
                debit_sum = 0.0
                credit_sum = 0.0
                emp_name.append(payslip.employee_id.name)
                if payslip.number:
                    slip_number.append(payslip.number)
                for line in payslip.details_by_salary_rule_category:
                    amount = payslip.credit_note and -line.total or line.total
                    if float_is_zero(amount, precision_digits=precision):
                        continue
                    debit_account_id = line.salary_rule_id.account_debit.id
                    credit_account_id = line.salary_rule_id.account_credit.id

                    if debit_account_id:
                        debit_line = (0, 0, {
                            'name': line.name,
                            'partner_id': False,
                            'account_id': debit_account_id,
                            'journal_id': payslip.journal_id.id,
                            'date': date,
                            'debit': amount > 0.0 and amount or 0.0,
                            'credit': amount < 0.0 and -amount or 0.0,
                            'analytic_account_id': line.salary_rule_id.analytic_account_id.id,
                            'tax_line_id': line.salary_rule_id.account_tax_id.id,
                        })
                        line_ids.append(debit_line)
                        debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']

                    if credit_account_id:
                        credit_line = (0, 0, {
                            'name': line.name,
                            'partner_id': payslip.employee_id.partner_id.id or False,
                            'account_id': credit_account_id,
                            'journal_id': payslip.journal_id.id,
                            'date': date,
                            'debit': amount < 0.0 and -amount or 0.0,
                            'credit': amount > 0.0 and amount or 0.0,
                            'analytic_account_id': line.salary_rule_id.analytic_account_id.id,
                            'tax_line_id': line.salary_rule_id.account_tax_id.id,
                        })
                        line_ids.append(credit_line)
                        credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']

                if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
                    acc_id = payslip.journal_id.default_credit_account_id.id
                    if not acc_id:
                        raise UserError(
                            _('The Expense Journal "%s" has not properly configured the Credit Account!') % (
                                payslip.journal_id.name))
                    adjust_credit = (0, 0, {
                        'name': _('Salary Payable'),
                        'partner_id': payslip.employee_id.partner_id.id or False,
                        'account_id': acc_id,
                        'journal_id': payslip.journal_id.id,
                        'date': date,
                        'debit': 0.0,
                        'credit': debit_sum - credit_sum,
                    })
                    line_ids.append(adjust_credit)

                elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
                    acc_id = payslip.journal_id.default_debit_account_id.id
                    if not acc_id:
                        raise UserError(_('The Expense Journal "%s" has not properly configured the Debit Account!') % (
                            payslip.journal_id.name))
                    adjust_debit = (0, 0, {
                        'name': _('Adjustment Entry'),
                        'partner_id': False,
                        'account_id': acc_id,
                        'journal_id': payslip.journal_id.id,
                        'date': date,
                        'debit': credit_sum - debit_sum,
                        'credit': 0.0,
                    })
                    line_ids.append(adjust_debit)
            name = 'Payslip of ' + ', '.join(emp_name)
            if slip_number:
                ref = ', '.join(slip_number)
            else:
                ref = self.name
            move_dict = {
                'narration': name,
                'ref': ref,
                'journal_id': self.journal_id.id,
                'date': date,
                'line_ids': line_ids,
            }
            if old_move:
                old_move.write(move_dict)
#                 old_move.post()
                for slip in payslip_rec:
                    slip.write({'move_id': old_move.id, 'date': date, 'state': 'done'})
            else:
                move = self.env['account.move'].sudo().create(move_dict)
#                 move.post()
                for slip in payslip_rec:
                    slip.write({'move_id': move.id, 'date': date, 'state': 'done'})

    @api.multi
    def action_set_batch_to_draft(self):
        """
        set payslip batch and all its payslip into draft state
        and cancel all related journal entry.
        :return:
        """
        for batch_slip in self:
            account_move_id = self.env['account.move'].sudo().search([('payslip_run_id', '=', batch_slip.id),
                                        ('state','=','posted')],limit=1)
            if account_move_id:
                raise UserError(_("You can't cancel batch payslip because Journal Entry already posted.!"))

            for slip_id in batch_slip.slip_ids:
                slip_id.with_context({'from_batch_payslip':True}).action_set_to_draft()
                if not self.env['ir.module.module'].sudo().search([('name', '=', 'account_cancel'), ('state', '=', 'installed')]):
                    raise UserError(_("Needs To Install \'Account Cancel\' Module"))
                if slip_id.move_id.journal_id.update_posted:
                    slip_id.move_id.button_cancel()
#                     slip_id.move_id.line_ids.unlink()
                    slip_id.move_id.with_context({'custom_move':True}).unlink()
                slip_id.write({'state': 'draft'})
            batch_slip.write({'state':'draft'})

    @api.multi
    def get_debit_move_line(self, debit_account_id, line, payslip, date, amount, analytic_account_id=None):
        """
        creates move line for payslip line that contains debit account
        :param debit_move_lines: dictionary containing move line
        :param debit_account_id: account_id
        :param line: current payslip line
        :param payslip: payslip object
        :param date: date of the payslip
        :param amount: amount to be debited
        :return: move line
        """
        debit_account_id = self.env['account.account'].sudo().browse(debit_account_id)
        if debit_account_id.user_type_id.name == 'Expenses' and not payslip.contract_id.analytic_account_id:
            raise UserError(_('cost centre is missing on the employee %s contract.' % (payslip.employee_id.display_name)))

        debit_move_lines = {
            'name': line.salary_rule_id.report_header_id.name if line.salary_rule_id.report_header_id else line.name,
            'partner_id': False,
            'analytic_account_id':analytic_account_id if debit_account_id.user_type_id.name == 'Expenses' else False,
            'account_id': debit_account_id.id,
            'journal_id': payslip.journal_id.id,
            'date': date,
            'debit': amount > 0.0 and amount or 0.0,
            'credit': amount < 0.0 and -amount or 0.0,
        }
        return debit_move_lines

    @api.multi
    def get_credit_move_line(self, credit_account_id, line, amount, payslip, date, analytic_account_id=None, header_name=None):
        """
        creates move line for payslip line that contains credit account and amount != 0.0
        :param credit_moves_line: dictionary containing credit move line
        :param credit_account_id:  account id
        :param line: current payslip line
        :param amount: amount to be credited
        :param payslip: payslip object
        :param date: date of payslip
        :return: credit move line
        """
        credit_account_id = self.env['account.account'].sudo().browse(credit_account_id)
        if credit_account_id.user_type_id.name == 'Expenses' and not payslip.contract_id.analytic_account_id:
            raise UserError(_('cost centre is missing on the employee %s contract.' % (payslip.employee_id.display_name)))

        credit_moves_line = {
            'name': header_name if header_name else line.name,
            'account_id': credit_account_id.id,
            'journal_id': payslip.journal_id.id or False,
            'date': date,
            'debit': amount > 0.0 and amount or 0.0,
            'credit': amount < 0.0 and -amount or 0.0,
            'analytic_account_id':analytic_account_id if credit_account_id.user_type_id.name == 'Expenses' else False,
            'tax_line_id': line.salary_rule_id.account_tax_id.id,
        }
        return credit_moves_line

    @api.multi
    def get_adjustment_credit_move_line(self, date, credit_move_amount, key=None):
        """
        creates credit journal item for employee as adjustment entry
        :param payslip:
        :param date:
        :param credit_move_amount:
        :return:
        """
        acc_id = self.journal_id.default_credit_account_id.id
        if not acc_id:
            raise UserError(
                _('The Expense Journal "%s" has not properly configured the Credit Account!') % (
                    self.journal_id.name))
        return {
            'name': _('Salary Payable'),
#             'partner_id': payslip.employee_id.partner_id.id or False,
            'account_id': acc_id,
            'journal_id': self.journal_id.id,
            'date': date,
            'analytic_account_id':key,
            'debit': 0.0,
            'credit': credit_move_amount,
        }

    @api.multi
    def action_view_entries(self):
        '''
        :return: View journal entry.
        '''
        self.ensure_one()
        form_view = self.env.ref('account.view_move_form', False)
        return {
            'name': _('Journal Entries'),
            'res_model': 'account.move',
            'res_id': self.account_move_id.id,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'context': self._context,
        }

    @api.multi
    def action_view_journal_items(self):
        '''
        :return: Journal item
        '''
        context = dict(self._context)
        action = self.env.ref('account.action_account_moves_all_a')
        account_move = self.env['account.move'].search([('payslip_run_id', '=', self.id)]).ids
        account_move.append(self.account_move_id.id)
        domain = [('move_id', 'in', account_move)]
        result = {
            'name': action.name,
            'type': action.type,
            'view_type': action.view_type,
            'view_mode': action.view_mode,
            'target': action.target,
            'context': context,
            'domain': domain,
            'res_model': action.res_model,
        }
        return result

    @api.multi
    def action_view_batch_entries(self):
        '''
        :return: View journal entries.
        '''
        self.ensure_one()
        context = dict(self._context)
        context['default_payslip_run_id'] = self.id
        action = self.env.ref('account.action_move_select')
        domain = [('payslip_run_id', '=', self.id)]
        result = {
            'name': action.name,
            'type': action.type,
            'view_type': action.view_type,
            'view_mode': action.view_mode,
            'target': action.target,
            'context': context,
            'res_model': action.res_model,
            'domain': domain,
        }
        return result

    @api.multi
    def action_to_pay(self):
        self.ensure_one()
        ctx = dict(self._context)
        payslip_records = self.env['hr.payslip'].search([('payslip_run_id', '=', self.id)])
        if any(payslip.state == 'paid' for payslip in payslip_records):
            raise UserError(_("Selected Batch few payslips has been already "
                              "paid!"))
        if any(payslip.state != 'done' for payslip in payslip_records):
            raise UserError(_("All the payslips must be Done!"))

        if any(not payslip.employee_id.journal_id.sudo() for payslip in payslip_records):
            raise UserError(_("Some employee have not set Payment Mode!"))

        group_by_emp_journal = {}
        for payslip in payslip_records:
            journal_id = payslip.employee_id.journal_id.sudo()
            if journal_id.id not in group_by_emp_journal:
                group_by_emp_journal.update({journal_id.id:payslip.net_amount})
            else:
                group_by_emp_journal[journal_id.id] += payslip.net_amount

        payment_line_lst = []
        for key, value in group_by_emp_journal.items():
            vals = {'journal_id': key, 'amount':value}
            payment_line_lst.append((0, 0, vals))

        ctx.update({'default_payment_line_ids':payment_line_lst})
        form_view = self.env.ref('bista_payroll.view_hr_payslip_payment_form')
        return {
            'name': 'Pay Payslip',
            'type': 'ir.actions.act_window',
            'view_id': form_view.id,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hr.payslip.payment',
            'target': 'new',
            'context': ctx,
        }

    @api.multi
    def unlink(self):
        for payslip in self:
            if payslip.state not in ('draft'):
                raise UserError(_(
                    'Cannot delete payslip which are in %s state' % (
                        payslip.state)))
        return super(HrPayslipRun, self).unlink()


class AccountMove(models.Model):
    _inherit = 'account.move'

    payslip_run_id = fields.Many2one('hr.payslip.run', string='Batch Payslip', copy=False)
