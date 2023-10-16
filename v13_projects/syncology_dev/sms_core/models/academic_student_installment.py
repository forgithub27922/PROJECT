# -*- encoding: utf-8 -*-
#######################################################################################
#
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#    Copyright (C) 2020 Skyscend Business Solutions  Pvt. Ltd.(<http://skyscendbs.com>)
#
#######################################################################################
from odoo import models, fields, api


class AcademicStudentInstallment(models.Model):
    _name = 'academic.student.installment'

    @api.depends('student_id.first_name_arabic', 'student_id.middle_name_arabic', 'student_id.second_middle_name_arabic', 'student_id.last_name_arabic')
    def _compute_student_name_arabic(self):
        for rec in self:
            rec.student_name_arabic = rec.student_id.full_name_arabic

    student_id = fields.Many2one('academic.student', 'Student')
    student_name_arabic = fields.Char(compute='_compute_student_name_arabic', string='Student Name Arabic', tracking=True, store=True)
    fee_policy_line_id = fields.Many2one('fee.policy.line', string="Fee Policy Line")
    student_fee_id = fields.Many2one('student.fee', string="Student Fee")
    fee_status = fields.Selection([('unpaid', 'Unpaid'), ('paid', 'Paid'),
                                   ('refunded', 'Refunded'), ('cancelled', 'Cancelled')],
                                  string='Fee Status', related='student_fee_id.status')

    name = fields.Char('Student Name', related='student_id.full_name')
    name_arabic = fields.Char('Student Name', related='student_id.full_name_arabic')
    class_id = fields.Many2one('school.class', string='Grade', related='student_id.class_id')
    school_id = fields.Many2one('schools.list', string='School', related='student_id.school_id')
    class_section_id = fields.Many2one('class.section', string='Section', related='student_id.class_section_id')
    national_id = fields.Char('National ID', related='student_id.national_id')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female'), ('other', 'Other')], string='Gender',
                              related='student_id.gender')
    religion = fields.Selection([('muslim', 'Muslim'), ('christian', 'Christian'), ('other', 'Other')],
                                string='Religion', related='student_id.religion')
    passport_id = fields.Char('Passport No', related='student_id.passport_id')
    state = fields.Selection(
        [('draft', 'Draft'), ('admitted', 'Admitted'), ('cancelled', 'Cancelled'), ('inactive', 'Inactive'),
         ('withdrawn', 'Withdrawn')], 'State', related='student_id.state')
    birth_date = fields.Date('Date of Birth', related='student_id.birth_date')
    birth_place = fields.Char('Birth Place', related='student_id.birth_place')
    city = fields.Many2one('res.city', related='student_id.city')
    address = fields.Text('Address', related='student_id.address')
    primary_language = fields.Char('Primary Language', related='student_id.primary_language')
    second_language = fields.Char('Second Language', related='student_id.second_language')
    father_full_name_arabic = fields.Char('Father Full Name Arabic', related='student_id.father_full_name_arabic')
    father_landline_number = fields.Char('Father Home Phone', related='student_id.father_landline_number')
    father_land_line_no = fields.Char('Father Work Phone', related='student_id.father_land_line_no')
    father_national_id = fields.Char('Father National ID', related='student_id.father_national_id')
    mother_full_name_arabic = fields.Char('Mother Full Name Arabic', related='student_id.mother_full_name_arabic')
    mother_national_id = fields.Char('Mother National ID', related='student_id.mother_national_id')
    mother_landline_number = fields.Char('Mother Home Phone', related='student_id.mother_landline_number')
    mother_land_line_no = fields.Char('Mother Work Phone', related='student_id.mother_land_line_no')
    guardian_full_name_arabic = fields.Char('Guardian Full Name Arabic', related='student_id.guardian_full_name_arabic')
    guardian_national_id = fields.Char('Guardian National ID', related='student_id.guardian_national_id')
    guardian_landline_number = fields.Char('Guardian Home Phone', related='student_id.guardian_landline_number')
    guardian_land_line_no = fields.Char('Guardian Work Phone', related='student_id.guardian_land_line_no')
    payment_status = fields.Selection([('not_paid', 'Not paid'), ('paid', 'Paid')], string='Payment Status',
                                      related='student_id.payment_status')
    date_of_apply = fields.Date('Date of Admission', related='student_id.date_of_apply')
    siblings_ids = fields.Many2many('academic.student', related='student_id.siblings_ids')

    # parent employee
    mother_employee_id = fields.Many2one('hr.employee', string='Mother Employee',
                                         related='student_id.mother_employee_id')
    father_employee_id = fields.Many2one('hr.employee', string='Father Employee',
                                         related='student_id.father_employee_id')

    def post_fees_installment(self):
        """
        This method is used to create student fee
        -----------------------------------------
        @param self: object pointer
        """
        fee_policy_line = self.env['fee.policy.line'].browse(self._context.get('student_id'))
        fees_obj = self.env['student.fee']

        for student in self:
            if student.state != 'payment':
                fees_vals = {}
                father = student.father_employee_id.id
                mother = student.mother_employee_id.id
                parent_emps = []
                if father:
                    parent_emps.append(father)
                if mother:
                    parent_emps.append(mother)
                fees_vals.update({'student_id': student.student_id.id,
                                  'due_date': fee_policy_line.due_date,
                                  'fee_date': fee_policy_line.date,
                                  'total_amount': fee_policy_line.amount,
                                  'fee_policy_line_id': fee_policy_line.id,
                                  'journal_id': fee_policy_line.journal_id.id,
                                  'from_account': fee_policy_line.from_account.id,
                                  'to_account': fee_policy_line.to_account.id,
                                  'grade_id': student.class_id.id,
                                  'admission_Date': student.date_of_apply,
                                  'siblings_ids': student.siblings_ids.ids,
                                  'mother_starting_date': student.mother_employee_id.starting_date,
                                  'father_starting_date': student.father_employee_id.starting_date,
                                  })
                if parent_emps:
                    fees_vals.update({
                        'parent_employee_ids': [(6, 0, parent_emps)]
                    })
                student_fee = fees_obj.create(fees_vals)
                student.write({'student_fee_id': student_fee.id})

    def delete_student(self):
        """
        This method is used to delete student installment and student fee which is not paid
        -----------------------------------------------------------------------------------
        @param self: object pointer
        """
        recipientData = []
        values = {'subject': 'Removed from Instalment'}
        mail_pool = self.env['mail.mail']
        fee_policy_line = self.env['fee.policy.line'].browse(self._context.get('student_id'))
        stud_fee_obj = self.env['student.fee']
        for student in self:
            stud = stud_fee_obj.search([('student_id', '=', student.id)])
            body_html = """<div>
            <p>Dear Mr.""" + str(student.student_id.first_name) + \
                        ' ' + str(student.student_id.middle_name) + \
                        ' ' + str(student.student_id.second_middle_name) + \
                        ' ' + str(student.student_id.last_name) + """,
            <br/>We kindly confirm that you have been relieved from the payment of  """ + \
                        str( fee_policy_line.amount) + """ has for """ + \
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
                    installment_list_lines = installment_list_lines + \
                                             str(fee.total_amount) + ' for ' + \
                                             str(fee.fee_type_id.name) + ' before ' + \
                                             str(fee.due_date) + '<br/>'
                    unpaid_records_total_amount = unpaid_records_total_amount + fee.total_amount
                body_html = body_html + installment_list + installment_list_lines
                body_html = body_html + '<br/>Total amount: ' + str(unpaid_records_total_amount )
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

        fee_policy_line = self.env['fee.policy.line'].browse(self._context.get('student_id'))
        fee_policy_line.write({'academic_student_installment_ids': [(3, self.id)]})
        self.student_fee_id.unlink()
