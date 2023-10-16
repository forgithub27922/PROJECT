from odoo import api, fields, models


class FeesInstallmentsWizard(models.TransientModel):
    _name = "fees.installments.wizard"
    _description = "Fees Installments Wizard"

    student_id = fields.Many2many('academic.student', string="Students")

    def fees_installment(self):
        student_installment_lst = []
        fee_policy_line = self.env['fee.policy.line'].browse(self._context.get('active_id'))
        for student in self.student_id.ids:
            student_installment_lst.append((0, 0, {'student_id': student}))

        fee_policy_line.write({'academic_student_installment_ids': student_installment_lst})
