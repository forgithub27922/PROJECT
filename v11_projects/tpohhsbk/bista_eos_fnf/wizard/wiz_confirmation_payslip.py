# -*- encoding: utf-8 -*-
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#

import calendar

from odoo import models, fields, api, tools, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError


class wiz_confirmation_payslip(models.TransientModel):
    _name = 'wiz.confirmation.payslip'

    def generate_payslips(self):
        """
        Generates payslip for last 2 months if not in draft state and
        gets payslip without batch payslip and state not in cancel.
        :return:
        """
        ctx = self._context.copy()
        eos_obj = self.env['hr.termination.request'].search([('id', '=', ctx.get('active_id'))])
        if not eos_obj.employee_id.contract_id:
            raise ValidationError("Please Configure Contract For The Employee.")
        if not eos_obj.employee_id.contract_id.journal_id.id:
            raise ValidationError("Please Configure Salary Journal on contract for %s" % eos_obj.employee_id.name)
        lst_month_fst_date = fields.Date.to_string(fields.Date.from_string(eos_obj.relieve_date)
                                                    + relativedelta(day=1, months=-1))
        lst_month_lst_date = fields.Date.to_string((fields.Date.from_string(eos_obj.relieve_date)
                                                    + relativedelta(day=1))
                                                   + relativedelta(days=-1))
        crnt_month_fst_date = fields.Date.to_string(fields.Date.from_string(eos_obj.relieve_date)
                                                   + relativedelta(day=1))
        worked_days = fields.Date.from_string(eos_obj.relieve_date).day
        crnt_month_lst_date = ((fields.Date.from_string(eos_obj.relieve_date) + relativedelta(day=1, months=1)) + relativedelta(days=-1))
        unpaid_payslip_ids = self.env['hr.payslip'].search([('employee_id', '=', eos_obj.employee_id.id),
                                                            ('payslip_run_id','=',False),
                                                            ('state', '=', 'done')])
        payslip_ids = self.env['hr.payslip'].search([('employee_id', '=', eos_obj.employee_id.id),
                                                     ('date_from','>=',lst_month_fst_date),
                                                     ('date_to','<=',lst_month_lst_date),
                                                     ('state', '!=', 'cancel'),
                                                     '|',('payslip_run_id','=',False),
                                                     ('payslip_run_id','!=',False)
                                                     ])
        current_month_payslip_id = self.env['hr.payslip'].search([('employee_id', '=', eos_obj.employee_id.id),
                                                     ('date_from','>=',crnt_month_fst_date),
                                                     ('date_to','<=',crnt_month_lst_date),
                                                     ('state', '!=', 'cancel'),
                                                     '|',('payslip_run_id','=',False),
                                                     ('payslip_run_id','!=',False)
                                                     ])

        if current_month_payslip_id:
            return
        last_payslip = payslip_ids[-1:]
        if not last_payslip or last_payslip.date_from < lst_month_fst_date:
            input_line_ids = self.get_inputs(eos_obj.employee_id.contract_id, 0.0)
            lst_month_slip_vals = {
                'name': _('Salary Slip of %s ') % (eos_obj.employee_id.name + ' for ' + calendar.month_name[
                    int(fields.Date.from_string(lst_month_fst_date).month)] + ' ' + str(
                    fields.Date.from_string(lst_month_fst_date).year)),
                'employee_id': eos_obj.employee_id.id,
                'contract_id': eos_obj.employee_id.contract_id.id or False,
                'struct_id': eos_obj.employee_id.contract_id.struct_id.id or False,
                'date_from': lst_month_fst_date,
                'date_to': lst_month_lst_date,
                'input_line_ids': input_line_ids,
                'journal_id': eos_obj.employee_id.contract_id.journal_id.id or False,
            }
            last_month_slip_id = self.env['hr.payslip'].create(lst_month_slip_vals)
            last_month_slip_id.onchange_employee()
            last_month_slip_id.compute_sheet()
            unpaid_payslip_ids += last_month_slip_id
        if not last_payslip or last_payslip.date_from < crnt_month_fst_date:
            crnt_month_slip_vals = {
                'name': _('Salary Slip of %s ') % (eos_obj.employee_id.name + ' for ' + calendar.month_name[
                    int(fields.Date.from_string(crnt_month_fst_date).month)] + ' ' + str(
                    fields.Date.from_string(crnt_month_fst_date).year)),
                'employee_id': eos_obj.employee_id.id,
                'contract_id': eos_obj.employee_id.contract_id.id,
                'struct_id': eos_obj.employee_id.contract_id.struct_id.id,
                'date_from': crnt_month_fst_date,
                'date_to': crnt_month_lst_date,
                'journal_id': eos_obj.employee_id.contract_id.journal_id.id or False,
            }
            crnt_month_slip_id = self.env['hr.payslip'].create(crnt_month_slip_vals)
            crnt_month_slip_id.with_context({'date_from': crnt_month_fst_date,
                                             'date_to':crnt_month_lst_date}).onchange_employee()
            crnt_month_slip_id.compute_sheet()
            non_payable_amount = crnt_month_slip_id.net_amount - ((crnt_month_slip_id.net_amount / crnt_month_lst_date.day) * worked_days)
            input_line_ids = self.get_inputs(eos_obj.employee_id.contract_id, non_payable_amount)
            crnt_month_slip_id.input_line_ids.unlink()
            crnt_month_slip_id.write({'input_line_ids': input_line_ids})
            crnt_month_slip_id.compute_sheet()
            unpaid_payslip_ids += crnt_month_slip_id

            # Comment Code for generate payslip in Draft State.
            # Not make it Paid. As we discussed with Dilya. 
            # for slip in unpaid_payslip_ids:
                # if slip.state == "draft":
                #     slip.sudo().action_payslip_done()
        eos_obj.write({'slip_ids': [(6, 0, unpaid_payslip_ids.ids)]})

    def get_inputs(self, contract, non_payable_amount):
        """
        sets leave deduction amount where it gets salary rule with is leave deduction = true.
        :param contract: employee contract
        :param non_payable_amount:
        :return:
        """
        res = []
        structure_ids = contract.get_all_structures()
        rule_ids = self.env['hr.payroll.structure'].browse(structure_ids).get_all_rules()
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x: x[1])]
        inputs = self.env['hr.salary.rule'].browse(sorted_rule_ids).mapped('input_ids')
        for input in inputs:
            input_data = {
                'name': input.name,
                'code': input.code,
                'contract_id': contract.id,
            }
            if input.input_id.is_leave_deduction:
                input_data['amount'] = non_payable_amount or 0.0
            res.append([0, 0, input_data])
        return res