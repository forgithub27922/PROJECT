# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class PostFeeInstallmentsWizard(models.TransientModel):
    _name = "post.fee.installment.wizard"
    _description = "Post Fee Installments Wizard"

    school_id = fields.Many2one('schools.list', 'School')
    grade_id = fields.Many2many('school.class', string='Grade', domain="[('school_id', '=', school_id)]")
    student_ids = fields.Many2many('academic.student', string='Student')
    type = fields.Selection([('post_to_grades', 'Post to Grades'), ('post_to_students', 'Post to Students')], string='Type', default='post_to_grades')
    deactivate_lms_on_due = fields.Boolean('Deactivate LMS on Due', default=False)
    pending_payment_students = fields.Boolean('Pending Payment Students')

    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)
    synced_with_lms = fields.Boolean('Synced with LMS', related='company_id.synced_with_lms')

    @api.onchange('synced_with_lms')
    def onchange_deactivate_lms_on_due(self):
        self.deactivate_lms_on_due = self.synced_with_lms

    def post_fee_installment(self):
        fee_policy_line_id = self.env['fee.policy.line'].browse(self._context.get('active_id'))
        fee_policy_line_id.state = 'post'
        fees_obj = self.env['student.fee']
        for students in self:
            if students.type == 'post_to_students' and students.pending_payment_students:
                student_installment_lst = []
                for student in students.student_ids:
                    if student.state != 'payment':
                        father = student.father_employee_id.id
                        mother = student.mother_employee_id.id
                        parent_emps = []
                        if father:
                            parent_emps.append(father)
                        if mother:
                            parent_emps.append(mother)
                        fees_vals = {
                            'student_id': student.id,
                            'due_date': fee_policy_line_id.due_date,
                           'fee_date': fee_policy_line_id.date,
                           'total_amount': fee_policy_line_id.amount,
                           'fee_policy_line_id': fee_policy_line_id.id,
                           'journal_id': fee_policy_line_id.journal_id.id,
                           'from_account': fee_policy_line_id.from_account.id,
                           'to_account': fee_policy_line_id.to_account.id,
                           'grade_id': student.class_id.id,
                           'admission_Date': student.date_of_apply,
                           'siblings_ids': student.siblings_ids.ids,
                            'mother_starting_date':student.mother_employee_id.starting_date,
                            'father_starting_date': student.father_employee_id.starting_date,
                        }
                        if parent_emps:
                            fees_vals.update({
                                'parent_employee_ids': [(6, 0, parent_emps)]
                            })
                        student_fee = fees_obj.create(fees_vals)
                        student_installment_lst.append((0, 0, {'student_id': student.id,
                                                               'student_fee_id': student_fee.id}))
                fee_policy_line_id.write({'academic_student_installment_ids': student_installment_lst})
            elif students.type == 'post_to_students':
                student_installment_lst = []
                for student in students.student_ids:
                    father = student.father_employee_id.id
                    mother = student.mother_employee_id.id
                    parent_emps = []
                    if father:
                        parent_emps.append(father)
                    if mother:
                        parent_emps.append(mother)
                    fees_vals = {
                        'student_id': student.id,
                        'due_date': fee_policy_line_id.due_date,
                        'fee_date': fee_policy_line_id.date,
                        'total_amount': fee_policy_line_id.amount,
                        'fee_policy_line_id': fee_policy_line_id.id,
                        'journal_id': fee_policy_line_id.journal_id.id,
                        'from_account': fee_policy_line_id.from_account.id,
                        'to_account': fee_policy_line_id.to_account.id,
                        'grade_id': student.class_id.id,
                        'admission_Date': student.date_of_apply,
                        'siblings_ids': student.siblings_ids.ids,
                        'mother_starting_date': student.mother_employee_id.starting_date,
                        'father_starting_date': student.father_employee_id.starting_date,
                    }
                    if parent_emps:
                        fees_vals.update({
                            'parent_employee_ids': [(6, 0, parent_emps)]
                        })
                    student_fee = fees_obj.create(fees_vals)
                    student_installment_lst.append((0, 0, {'student_id': student.id,
                                                           'student_fee_id': student_fee.id}))

                fee_policy_line_id.write({'academic_student_installment_ids': student_installment_lst})
            elif students.type == 'post_to_grades' and students.pending_payment_students:
                student_installment_lst = []
                student_rec = self.env['academic.student'].search([('class_id', 'in', students.grade_id.ids),
                                                                   ('school_id', '=', self.school_id.id),
                                                                   ('state', 'in', ('draft', 'admitted'))])
                for student in student_rec:
                    father = student.father_employee_id.id
                    mother = student.mother_employee_id.id
                    parent_emps = []
                    if father:
                        parent_emps.append(father)
                    if mother:
                        parent_emps.append(mother)
                    fees_vals = {
                        'student_id': student.id,
                        'due_date': fee_policy_line_id.due_date,
                        'fee_date': fee_policy_line_id.date,
                        'total_amount': fee_policy_line_id.amount,
                        'fee_policy_line_id': fee_policy_line_id.id,
                        'journal_id': fee_policy_line_id.journal_id.id,
                        'from_account': fee_policy_line_id.from_account.id,
                        'to_account': fee_policy_line_id.to_account.id,
                        'grade_id': student.class_id.id,
                        'admission_Date': student.date_of_apply,
                        'siblings_ids': student.siblings_ids.ids,
                        'mother_starting_date': student.mother_employee_id.starting_date,
                        'father_starting_date': student.father_employee_id.starting_date,
                    }
                    if parent_emps:
                        fees_vals.update({
                            'parent_employee_ids': [(6, 0, parent_emps)]
                        })
                    student_fee = fees_obj.create(fees_vals)
                    student_installment_lst.append((0, 0, {'student_id': student.id,
                                                           'student_fee_id': student_fee.id}))
                fee_policy_line_id.write({'academic_student_installment_ids': student_installment_lst})
            elif students.type == 'post_to_grades':
                student_installment_lst = []
                student_rec = self.env['academic.student'].search([('class_id', 'in', students.grade_id.ids),
                                                                   ('school_id', '=', self.school_id.id),
                                                                   ('state', '=', 'admitted')])

                for student in student_rec:
                    father = student.father_employee_id.id
                    mother = student.mother_employee_id.id
                    parent_emps = []
                    if father:
                        parent_emps.append(father)
                    if mother:
                        parent_emps.append(mother)
                    fees_vals = {
                        'student_id': student.id,
                        'due_date': fee_policy_line_id.due_date,
                        'fee_date': fee_policy_line_id.date,
                        'total_amount': fee_policy_line_id.amount,
                        'fee_policy_line_id': fee_policy_line_id.id,
                        'journal_id': fee_policy_line_id.journal_id.id,
                        'from_account': fee_policy_line_id.from_account.id,
                        'to_account': fee_policy_line_id.to_account.id,
                        'grade_id': student.class_id.id,
                        'admission_Date': student.date_of_apply,
                        'siblings_ids': student.siblings_ids.ids,
                        'mother_starting_date': student.mother_employee_id.starting_date,
                        'father_starting_date': student.father_employee_id.starting_date,
                    }
                    if parent_emps:
                        fees_vals.update({
                            'parent_employee_ids': [(6, 0, parent_emps)]
                        })
                    student_fee = fees_obj.create(fees_vals)
                    student_installment_lst.append((0, 0, {'student_id': student.id,
                                                           'student_fee_id': student_fee.id}))

                fee_policy_line_id.write({'academic_student_installment_ids': student_installment_lst})
