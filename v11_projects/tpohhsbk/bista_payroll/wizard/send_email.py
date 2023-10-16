from odoo import fields, models, api, _
from odoo.exceptions import UserError


class SendPayslip(models.TransientModel):
    _name = 'send.payslip.email'
    _description = 'Send Email'

    @api.multi
    def send_payslip(self):
        ctx = dict(self._context)
        if ctx and ctx.get('active_id'):
            payslip_rec = self.env['hr.payslip'].browse(ctx.get('active_id'))
            template = self.env.ref('bista_payroll.payslip_send_email',
                                    raise_if_not_found=False)
            if not template:
                raise UserError(
                    _('The Payslip Email Template is not in the database'))
            payslip_rec.send_payslip_email(template)
