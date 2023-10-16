# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models
from odoo.addons.bista_hijri_date.models.hijri import Convert_Date
from odoo.exceptions import ValidationError
from datetime import datetime
from dateutil.relativedelta import relativedelta


class HrTerminationRequest(models.Model):
    _name = 'hr.termination.request'
    _inherit = ['mail.thread']
    _description = "Terminate Request"
    _rec_name = 'employee_id'

    name = fields.Char('Description')
    employee_id = fields.Many2one(
        'hr.employee', 'Employee', ondelete="cascade")
    emp_id = fields.Char(related="employee_id.emp_id", string='Employee ID')
    department_id = fields.Many2one(related="employee_id.department_id")
    manager_id = fields.Many2one(related="employee_id.parent_id",
                                 string='Manager')
    date = fields.Date('Date')
    date_hijri = fields.Char(size=10)
    reason = fields.Text('Reason')
    comments = fields.Text('Comments')
    type = fields.Selection([('voluntary', 'Resignation'),
                             ('forced', 'Termination')],
                            string='Type of Separation')
    state = fields.Selection([('draft', 'Draft'),
                              ('submit', 'Submit'),
                              ('notice', 'Notice Period'),
                              ('approve_hr', 'Approve by HR'),
                              ('no_dues', 'No Dues'),
                              ('paid', 'Paid'),
                              ('retained', 'Retained'),
                              ('released', 'Released')],
                             default='draft',
                             track_visibility='onchange')
    relieve_date = fields.Date(string="Relieve Date")
    notice_period = fields.Integer(string="Notice Period In Days", default=30)
    pay_off_amount = fields.Float(string="Pay off Amount")
    employee_asset_ids = fields.One2many(
        comodel_name='employee.assets',
        inverse_name='termination_id', string='Assets')
    asset_penalty_account_id = fields.Many2one('account.account', string='Asset Penalty Account')
    hr_document_ids = fields.One2many('applicant.hr.document', 'exit_req_id',
                                      string="Documents")
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)

    @api.constrains('employee_id')
    def check_exit_request(self):
        exit_recs = self.search([
            ('employee_id', '=', self.employee_id.id),
            ('id', '!=', self.id),
            ('state', 'in', ('draft', 'submit', 'approve_hr', 'exit_interview',
                             'notice', 'no_dues'))])
        if exit_recs:
            raise ValidationError("You can not create multiple exit request!")


    @api.multi
    def send_intimation(self, template_id=False):
        """
        Send intimation to management department and exit request
        initiator
        :param template_id: mail template in string
        :return: None
        """
        for rec in self:
            template_id = self.env.ref(template_id)
            hr_manager = self.env.ref('hr.group_hr_manager')
            sudo_emp = rec.employee_id.sudo()
            email_to_users = \
                hr_manager.users + sudo_emp.parent_id.user_id + \
                sudo_emp.user_id
            email_to_users = email_to_users.filtered(lambda i: i.email)
            email_to = email_to_users.mapped('email')
            if email_to:
                template_id.write({'email_to': list(set(email_to))})
                template_id.send_mail(rec.id, force_send=True)


    @api.multi
    def state_submit(self):
        """
        Set request state to submit
        :return: None
        """
        for rec in self:
            rec.state = 'submit'
            rec.send_intimation('bista_eos.termination_req_approval_template')

    @api.multi
    def state_approve_manager(self):
        """
        Set request state to notice once manager is approved,
        Show validation if exit request initiator has not manager set and
        try to approve himself/herself
        :return: None
        """
        for rec in self:
            if self._uid == rec.employee_id.user_id.id:
                raise ValidationError("You can not approve your exit request!")
            rec.state = 'notice'
            rec.employee_id.write({'status': 'notice_period',
                                   'is_notice_period': True,
                                   'status_history': [
                                       (0, 0,
                                        {'start_date': datetime.now().date(),
                                         'end_date': datetime.now().date(),
                                         'state': 'notice_period'
                                   })]
                                   })
            rec.send_intimation('bista_eos.termination_req_approval_template')

    @api.multi
    def state_approve_hr(self):
        """
        Set request state to Approve by HR once HR manager will approve
        :return: None
        """
        for rec in self:
            rec.state = 'approve_hr'
            # rec.send_intimation('bista_eos.termination_req_approval_template')

    @api.multi
    def state_no_dues(self):
        """
        Set request state to no dues (Asset check)
        :return: None
        """
        for rec in self:
            asset_data = []
            for asset in rec.employee_id.employee_asset_ids:
                vals = {
                    'termination_id': self.id,
                    'asset_id': asset.asset_id.id,
                    'receive_date': asset.receive_date,
                    'recover_date': asset.recover_date,
                    'penalties': asset.penalties,
                }
                asset_data.append(vals)
            self.employee_asset_ids = asset_data
            rec.state = 'no_dues'

    @api.multi
    def state_released(self):
        """
        set to release state once no dues is completed
        :return: None
        """
        for rec in self:
            rec.state = 'released'
            rec.employee_id.contract_id.state = 'close'
            # rec.employee_id.type = rec.type
            rec.employee_id.write({
                'type': rec.type,
                'status': 'relieved',
                'active':False,
                'status_history': [(0, 0, {'state': 'relieved',
                                           'start_date': datetime.now().date(),
                                           'end_date': datetime.now().date()
                                           })]
            })

    @api.multi
    def state_retained(self):
        """
        Set request state to Reject
        :return: wizard of reject request.
        """
        view_id = self.env.ref('bista_eos.wiz_view_reject_req_form')
        return {
            'name': 'Retained Request',
            'type': 'ir.actions.act_window',
            'view_id': view_id.id,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wiz.reject.request',
            'target': 'new',
        }

    @api.onchange('date', 'notice_period')
    def onchange_gregorian_date(self):
        """
        Convert Gregorian date to Hijri
        :return: None
        """
        self.ensure_one()
        if self.date:
            self.date_hijri = Convert_Date(
                self.date, 'english', 'islamic')

        if self.notice_period and self.date:
            date = fields.Date.from_string(self.date) + relativedelta(
                days=self.notice_period)
            self.relieve_date = fields.Date.to_string(date)

    @api.onchange('date_hijri')
    def onchange_hijri_date(self):
        """
        Convert Hijri date to Gregorian
        :return: None
        """
        self.ensure_one()
        if self.date_hijri:
            if self.date_hijri[4] != '-' or self.date_hijri[7] != '-':
                raise ValidationError(
                    "Incorrect date format, should be YYYY-MM-DD")
            self.date = Convert_Date(
                self.date_hijri, 'islamic', 'english')

    @api.constrains('notice_period')
    def _constraint_notice_period(self):
        """
        constraints for notice period
        :return: None
        """
        if self.notice_period < 0 or not isinstance(self.notice_period, int):
            raise ValidationError('Please enter integer value for '
                                  'notice period in days!')


class ApplicantHRDocument(models.Model):
    _inherit = 'applicant.hr.document'

    exit_req_id = fields.Many2one('hr.termination.request',
                                  string="Exit Interview")

    @api.multi
    def get_report(self):
        """
        Print hr documents like appointment letter, offer letter etc.
        :return: report action
        """
        hr_doc = self.env['hr.job.document'].browse(self.document_id.id)
        if self.document_id and self.exit_req_id and \
            self.exit_req_id.employee_id:
            hr_doc.employee_id = self.exit_req_id.employee_id.id
        return self.env.ref(
            'hr_document.report_offer_letter').report_action(hr_doc)
