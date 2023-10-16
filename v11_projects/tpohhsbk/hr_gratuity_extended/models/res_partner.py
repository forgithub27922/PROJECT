# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import fields, models, api
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError
from odoo.tools import float_round
import calendar


class GratuityAccrualLine(models.Model):
    _inherit = 'gratuity.accrual.line'

    @api.model
    def automatic_hr_past_gratuity_calculation(self,company=False,start_date=False):
        """
        Generates gratuity automatic for previous month of employees
        :return:
        """
        gtt_accrual_exception_obj = self.env['gratuity.accrual.exception']
        company_domain = []
        if company:
            company_domain.append(('id','=',company))
        company_ids = self.env['res.company'].sudo().search(company_domain)
        for company in company_ids:
            if not company.gratuity_journal_id:
                desc = 'Please configure gratuity journal on company %s ' % company.name
                grt_jrn_exp_id = gtt_accrual_exception_obj.search([('company_id', '=', company.id),
                                                                   ('description', '=', desc)])
                if not grt_jrn_exp_id:
                    grty_missing_jrnl_vals = {
                        'employee_id': False,
                        'company_id': company.id or False,
                        'description': desc,
                        'date': fields.date.today(),
                    }
                    gtt_accrual_exception_obj.create(grty_missing_jrnl_vals)
                continue
            if not company.gratuity_account_id:
                desc = 'Please configure gratuity expense account on company %s ' % company.name
                grt_acnt_exp_id = gtt_accrual_exception_obj.search([('company_id', '=', company.id),
                                                                    ('description', '=', desc)])
                if not grt_acnt_exp_id:
                    grty_missing_exp_ac_vals = {
                        'employee_id': False,
                        'company_id': company.id or False,
                        'description': desc,
                        'date': fields.date.today(),
                    }
                    gtt_accrual_exception_obj.create(grty_missing_exp_ac_vals)
                continue
            employee_ids = self.env['hr.employee'].search([('status', 'not in', ['relieved', 'terminated', 'rejoined']),
                                                           ('company_id', '=', company.id)])
            gratuity_id = self.env['hr.gratuity'].search([('company_id', '=', company.id)])
            if not gratuity_id:
                desc = 'Gratuity configure missing for the company %s ' % company.name
                grt_config_exp_id = gtt_accrual_exception_obj.search([('company_id', '=', company.id),
                                                                      ('description', '=', desc)])
                if not grt_config_exp_id:
                    grty_config_exp_vals = {
                        'employee_id': False,
                        'company_id': company.id or False,
                        'description': desc,
                        'date': fields.date.today(),
                    }
                    gtt_accrual_exception_obj.create(grty_config_exp_vals)
                continue
            for employee in employee_ids:
                if employee.date_employment:
                    gtt_acrl_exc_id = gtt_accrual_exception_obj.search([('employee_id', '=', employee.id),
                                                                        ('company_id', '=', employee.company_id.id),
                                                                        ('description', '=', "Contract does not Exist")])
                    if not employee.contract_id and not gtt_acrl_exc_id:
                        gtt_accrual_exception_vals = {
                            'employee_id': employee.id,
                            'company_id': employee.company_id.id or False,
                            'description': "Contract does not Exist",
                            'date': fields.date.today(),
                        }
                        gtt_accrual_exception_obj.create(gtt_accrual_exception_vals)
                        continue
                    elif not employee.contract_id and gtt_acrl_exc_id:
                        continue
                    elif employee.contract_id and gtt_acrl_exc_id:
                        gtt_acrl_exc_id.unlink()
                    employee_gratuity = self.env['res.partner.gratuity.accrual'].search([('employee_id', '=', employee.id),('company_id','=',company.id)],limit=1)
                    if not employee_gratuity:
                        gratuity_vals = {
                            'employee_id': employee.id,
                            'state': 'accrual',
                            'company_id': employee.company_id.id,
                        }
                        employee_gratuity = self.env['res.partner.gratuity.accrual'].create(gratuity_vals)

                    is_exist_gratuity_line = self.search([('gtt_accrual_id','=',employee_gratuity.id)],order='id desc',limit=1)
                    # Start Date will set manually from cronjob
                    if start_date:
                        employment_date = fields.Date.from_string(start_date)
                    # If any existing gratuity line is there then get the end date and new accrual line will calculate from
                    # existing line end date + 1
                    elif is_exist_gratuity_line:
                        employment_date = fields.Date.from_string(is_exist_gratuity_line.end_date)
                        employment_date = employment_date + relativedelta(days=+1)
                    else:
                        employment_date = fields.Date.from_string(employee.date_employment)
                    has_next_month = True
                    gratuity_started = False
                    new_date = employment_date

                    while (has_next_month == True):
                        if new_date <= fields.Date.from_string(fields.Date.today()) and \
                            not new_date.year == fields.Date.from_string(fields.Date.today()).year or \
                            not new_date.month == fields.Date.from_string(fields.Date.today()).month:
                            if is_exist_gratuity_line:
                                current_month_last_date = new_date + relativedelta(months=+1,day=1,days=-1)
                                emp_experience = self.get_experience(employment_date, current_month_last_date, employee)
                            else:
                                emp_experience = self.get_experience(employment_date, new_date, employee)
                            gratuity_line_ids = self.env['hr.gratuity']

                            if new_date <= fields.Date.from_string(gratuity_id.date) and \
                                    employee.country_id.id == company.country_id.id:
                                gratuity_line_ids = gratuity_id.nationality_ids
                            elif new_date <= fields.Date.from_string(gratuity_id.date) and \
                                    employee.country_id.id != company.country_id.id:
                                gratuity_line_ids = gratuity_id.other_nationality_ids
                            elif new_date > fields.Date.from_string(gratuity_id.date):
                                gratuity_line_ids = gratuity_id.termination_contract_ids

                            for gratuity in gratuity_line_ids:
                                if emp_experience >= gratuity.from_experience and \
                                        emp_experience < gratuity.to_experience:
                                    new_date = self.create_accrual_line(gratuity, employee, new_date, False)
                                    gratuity_started = True
                                elif emp_experience >= gratuity.from_experience and \
                                        gratuity.to_experience == 0.0:
                                    new_date = self.create_accrual_line(gratuity, employee, new_date, False)
                                    gratuity_started = True
                            if not gratuity_started:
                                new_date = new_date + relativedelta(months=+1)
                        else:
                            has_next_month = False
                    self._cr.commit()

    def get_experience(self, employment_date, new_date,employee):
        """
        Finds experience of particular employee on date specified.
        :param employment_date:
        :param new_date:
        :return:
        """
        experience = 0.0
        rd = relativedelta(new_date, fields.Date.from_string(employee.date_employment))
        if rd.years or rd.months:
            experience = (rd.years) + (rd.months / 12)
        return experience

    def create_accrual_line(self, gratuity, employee, new_date, start_date):
        """
        Calculate accrual monthly of particular employee eos_fnf
        :param gratuity:
        :param employee:
        :param new_date:
        :param start_date:
        :return:
        """
        gratuity_days = 0.0
        amount = 0.0

        if (new_date.year % 4) == 0:
            starting_day = new_date.day - 1
            month_days = (calendar.monthrange(new_date.year, new_date.month)[1]) - starting_day
            if gratuity.allowed_gratuity_days:
                gratuity_days = gratuity.allowed_gratuity_days
            else:
                gratuity_days = float_round(((month_days
                                 * gratuity.days) / 366), precision_rounding=0.01)
            amount = ((employee.contract_id.wage * 12) / 366) * gratuity_days
            ed = new_date + relativedelta(day=calendar.monthrange(new_date.year, \
                                                                  new_date.month)[1])
        else:
            gratuity_config_date = fields.Date.from_string(gratuity.gratuity_id.date)
            if new_date.month == gratuity_config_date.month and \
                    new_date.year == gratuity_config_date.year and new_date < gratuity_config_date:
                if gratuity.allowed_gratuity_days:
                    gratuity_days = gratuity.allowed_gratuity_days
                else:
                    gratuity_days = float_round(((gratuity_config_date.day
                                              * gratuity.days) / 365), precision_rounding=0.01)
                amount = ((employee.contract_id.wage * 12) / 365) * gratuity_days
                ed = new_date + relativedelta(day=gratuity_config_date.day)
            else:
                starting_day = new_date.day - 1
                month_days = (calendar.monthrange(new_date.year, new_date.month)[1]) - starting_day
                if gratuity.allowed_gratuity_days:
                    gratuity_days = gratuity.allowed_gratuity_days
                else:
                    gratuity_days = float_round(((month_days
                                     * gratuity.days) / 365), precision_rounding=0.01)
                amount = ((employee.contract_id.wage * 12) / 365) * gratuity_days

                ed = new_date + relativedelta(day=calendar.monthrange(new_date.year, \
                                                                      new_date.month)[1])
        emp_gratuity = self.env['res.partner.gratuity.accrual'].search([('employee_id','=',employee.id)])
        is_exist_gratuity_line = self.search([('gtt_accrual_id','=',emp_gratuity.id),
                                            ('start_date', '=',new_date),
                                             ('end_date', '=', ed)])
        if not is_exist_gratuity_line:
            debit_vals = {
                'name': 'Gratuity Accrual',
                'debit': amount,
                'credit': 0.0,
                'analytic_account_id':employee.contract_id.analytic_account_id.id,
                'account_id': employee.company_id.gratuity_account_id.id or False,
                'partner_id': employee.partner_id.id or False,
            }
            credit_vals = {
                'debit': 0.0,
                'credit': amount,
                'account_id': employee.company_id.gratuity_journal_id. \
                                  default_credit_account_id.id or False,
                'partner_id': employee.partner_id.id or False,
            }
            vals = {
                'journal_id': employee.company_id.gratuity_journal_id.id,
                'date': fields.date.today(),
                'state': 'draft',
                'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)],
                'ref': 'Gratuity Accrual'
            }
            move = self.env['account.move'].create(vals)
            vals = {
                'gratuity_days':gratuity_days,
                'start_date':new_date,
                'end_date': ed,
                'gratuity_amount':amount,
                'account_move_id': move.id,
                'gtt_accrual_id': emp_gratuity.id,
            }
            self.create(vals)

        start_date = ed + relativedelta(days=+1)
        return start_date
