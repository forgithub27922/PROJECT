from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class RescheduleInstallment(models.TransientModel):
    _name = 'reschedule.installment.wizard'

    date_to_schedule = fields.Date(string='Date')

    @api.multi
    def reschedule_installment(self):
        # today_date = datetime.now().date()
        installment = self.env['loan.installments'].browse(
            self._context.get('loan_installment'))

        if installment:
            installment.write({'prev_due_date': installment.due_date,
                               'due_date': self.date_to_schedule,
                               'state': 'lock'})
        # Temporary Commented  code to check past date for SBK Only.
        # As SBK is clearing their past payroll entries.
        # if datetime.strptime(self.date_to_schedule, '%Y-%m-%d').date() < today_date:
        #     raise ValidationError("Past date is not allowed!.")
        # else:
        #     if  installment:
        #         installment.write({'prev_due_date': installment.due_date,
        #                            'due_date': self.date_to_schedule,
        #                            'state': 'lock'})
