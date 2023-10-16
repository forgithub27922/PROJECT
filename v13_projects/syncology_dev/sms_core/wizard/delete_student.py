# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class AdmissionListWizard(models.TransientModel):
    _name = "delete.student.wizard"
    _description = "Delete Student wizard"

    academic_student_installment_ids = fields.Many2many('academic.student.installment', string="Student")

    def delete_student(self):
        stud_lst = []
        recipientData = []
        values = {'subject': 'Removed from Instalment'}
        mail_pool = self.env['mail.mail']
        stud_fee_obj = self.env['student.fee']
        fee_policy_line = self.env['fee.policy.line'].browse(self._context.get('active_id'))
        for student in self.academic_student_installment_ids:
            stud_lst.append((3, student.id))
            stud = stud_fee_obj.search([('student_id', '=', student.id)])
            body_html = """<div>
            <p>Dear Mr.""" + str(student.student_id.first_name) + ' ' + \
                        str(student.student_id.middle_name) + ' ' + \
                        str(student.student_id.second_middle_name) + ' ' + \
                        str(student.student_id.last_name) + """,
            <br/>We kindly confirm that you have been relieved from the payment of  """ + \
                        str(fee_policy_line.amount) + """ has for """ + \
                        str(fee_policy_line.fee_type_id.name) + """ on """ + \
                        str(stud.payment_date) + """<br/></p>
            </div>"""
            unpaid_records = stud_fee_obj.search([('student_id', '=', student.student_id.id), ('status', '=', 'unpaid'),
                                                  ('id', '!=', student.student_fee_id.id)])
            if unpaid_records:
                installment_list = '<br/> We would also like to kindly remind you of the other due amounts: <br/>'
                installment_list_lines = ''
                unpaid_records_total_amount = 0.0
                for fee in unpaid_records:
                    installment_list_lines = installment_list_lines + str(fee.total_amount) + ' for ' + str(fee.fee_type_id.name) + ' before ' + str(fee.due_date) + '<br/>'
                    unpaid_records_total_amount = unpaid_records_total_amount + fee.total_amount
                body_html = body_html + installment_list + installment_list_lines
                body_html = body_html + '<br/>Total amount: ' + str(unpaid_records_total_amount)
                body_html = body_html + '<br/> Thank you for taking the time to look into this. We wish you a pleasant day.'
            if student.student_id.father_email:
                recipientData.append(student.student_id.father_email)
            if student.student_id.mother_email:
                recipientData.append(student.student_id.mother_email)
            if student.student_id.guardian_email:
                recipientData.append(student.student_id.guardian_email)
            values.update({'email_to': ','.join(recipientData)})
            values.update({'body_html': body_html})
            values.update({'body': body_html})
            msg_id = mail_pool.create(values)
            if msg_id:
                    msg_id.send()
        fee_policy_line.write({'academic_student_installment_ids': stud_lst})
        self.academic_student_installment_ids.student_fee_id.unlink()
