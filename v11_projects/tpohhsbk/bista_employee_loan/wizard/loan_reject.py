from datetime import datetime

from odoo import fields, models, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as OE_DTFORMAT


class LoanReject(models.TransientModel):
    _name = 'loan.reject.reason'
    _description = 'Loan Reject Reason'

    name = fields.Text(string='Reject Reason')

    @api.multi
    def reject_loan_request(self):
        """
        this method is called for reject loan request and add reject reason
        """
        ctx = dict(self._context)
        employee_loan_ids = False

        if ctx.get('active_model') == 'batch.employee.loan' and ctx.get('active_id'):
            batch_loan_id = self.env['batch.employee.loan'].browse(ctx.get('active_id'))
            batch_loan_id.reject_reason = self.name
            employee_loan_ids = batch_loan_id.employee_loan_ids
        
        if ctx.get('active_model') == 'hr.employee.loan' and ctx.get('active_id'):
            employee_loan_ids = self.env['hr.employee.loan'].browse(ctx.get('active_id'))

        if employee_loan_ids:
            for loan in employee_loan_ids:
                loan.write({'state': 'rejected'})
                ctx.update({'reject_reason': self.name})
                loan.with_context(ctx).send_email_notification(
                    'loan_request_rejected',
                    'hr.employee.loan', str(loan.employee_id.work_email))
                loan.loan_installment_ids.write({'state': 'reject'})
                reject_from = ctx.get('reject_from')
                if reject_from:
                    message = ('''<ul class="o_mail_thread_message_tracking">
                    <li>Loan Reject
                    Date Date: %s</li>
                    <li>Loan Number: %s </li>
                    <li>Rejected By: %s </li>
                    <li>Rejecte Reason: %s </li>
                        </ul>''') % (datetime.now().strftime(OE_DTFORMAT),
                                    loan.name, reject_from, self.name)
                    loan.message_post(body=message)
                    loan.reject_reason = self.name
