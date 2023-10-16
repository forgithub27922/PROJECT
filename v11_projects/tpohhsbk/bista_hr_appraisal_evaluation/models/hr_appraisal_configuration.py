import calendar
import datetime
import math
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF


class HrAppraisalConfiguration(models.Model):
    _name = 'hr.appraisal.configuration'

    name = fields.Char(string='Name')
    appraisal_policy = fields.Selection(
        string="Appraisal Policy", selection=[
            ('month', 'Monthly'), ('quarterly', 'Quarterly'),
            ('half_yearly', 'Half-Yearly'),
            ('annually', 'Annually')])
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    app_eval_ids = fields.One2many(
        'hr.appraisal.configuration.period', 'appraisal_template_id',
        string="Appraisal Period")
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.user.company_id)
    state = fields.Selection([
        ('draft', 'Draft'), ('in_progress', 'In Progress'),
        ('done', 'Closed')],
        string='Status', default='draft')
    no_of_appraisal = fields.Integer(compute='count_no_of_appraisal')

    @api.constrains('start_date', 'end_date')
    def date_validation(self):
        """
        date validation
        :return:
        """
        # if (datetime.datetime.strptime(self.start_date, DF).year) != \
        #         (datetime.datetime.strptime(self.end_date, DF).year):
        #     raise ValidationError(
        #         'Appraisal start date and end date should be from same
        # year!')
        if self.end_date < self.start_date:
            raise ValidationError(
                'The start date must be anterior to the end date.')

    @api.constrains('appraisal_policy', 'start_date', 'end_date')
    def appraisal_policy_validation(self):
        if self.appraisal_policy == 'quarterly':
            self.generate_appraisal_period(2)
        elif self.appraisal_policy == 'half_yearly':
            self.generate_appraisal_period(5)
        elif self.appraisal_policy == 'annually':
            self.generate_appraisal_period(11)

    def add_months(self, source_date, months, day_of_month):
        """
        add months as par specified into the provided date.
        also gets day of the month minimum or maximum.
        :param source_date:
        :param months:
        :param day_of_month:
        :return: datetime
        """
        month = source_date.month - 1 + months
        year = source_date.year + month // 12
        month = month % 12 + 1
        if day_of_month == 'max':
            day = max(source_date.day, calendar.monthrange(year, month)[1])
        elif day_of_month == 'min':
            day = 1
        return datetime.datetime(year, month, day)

    def generate_appraisal_period(self, policy):
        start_date = datetime.datetime.strptime(self.start_date,
                                                DF).replace(day=1)
        end_date = datetime.datetime.strptime(self.end_date, DF)
        end_date = end_date.replace(day=max(end_date.day,
                                            calendar.monthrange(
                                                end_date.year,
                                                end_date.month)[1]))
        appraisal_quarters = {}
        generate_appraisal = True
        count = 1
        while (generate_appraisal):
            appraisal_quarters['start_date' + str(count)] = start_date
            quarter_end_date = self.add_months(start_date, policy, 'max')
            if quarter_end_date <= end_date:
                appraisal_quarters['end_date' + str(count)] = \
                    quarter_end_date
                if quarter_end_date == end_date:
                    break
                else:
                    start_date = self.add_months(quarter_end_date, 1,
                                                 'min')
                    count += 1
            else:
                generate_appraisal = False

        keys = appraisal_quarters.keys()
        if 'end_date' + str(count) not in keys:
            raise ValidationError(
                "Start date and end date does not feat into selected "
                "appraisal policy")
        else:
            return appraisal_quarters

    def get_appraisal_period(self, current_month_sd, period_type):
        period_vals_list = []
        appraisal_quarters = self.generate_appraisal_period(period_type)
        for quarter in range(1, math.floor((len(appraisal_quarters) / 2)) + 1):
            start_date = appraisal_quarters[
                'start_date' + str(quarter)]
            end_date = appraisal_quarters['end_date' + str(quarter)]
            name = 'Appraisal Cycle %s' % (quarter)

            vals = {
                'name': name,
                'date_start': start_date.date(),
                'date_end': end_date.date(),
                'state': 'done'}

            if start_date >= current_month_sd or \
                    (current_month_sd > start_date and
                     current_month_sd <= end_date):
                vals.update({'state': 'in_progress'})
            period_vals_list.append((0, 0, vals))
        return period_vals_list

    @api.multi
    def appraisal_configuration_confirm(self):
        """
        generate period line and move in progress state.
        :return:
        """
        period_vals_list = []
        for rec in self:
            # Monthly
            current_month_sd = datetime.datetime.now().replace(day=1)

            if rec.appraisal_policy == 'month':
                start_date = datetime.datetime.strptime(
                    self.start_date, DF).replace(day=1)
                end_date = datetime.datetime.strptime(self.end_date, DF)
                end_date = end_date.replace(day=max(
                    end_date.day, calendar.monthrange(
                        end_date.year, end_date.month)[1]))
                last_date = start_date.replace(day=max(
                    start_date.day, calendar.monthrange(
                        start_date.year, start_date.month)[1]))
                create_period = True
                period_serial = 1
                while (create_period):
                    if last_date <= end_date:
                        name = 'Appraisal Cycle %s' % (period_serial)
                        vals = {'name': name, 'date_start': start_date.date(),
                                'date_end': last_date.date()}
                        if start_date.date() < current_month_sd.date():
                            vals.update({'state': 'done'})
                        period_vals_list.append((0, 0, vals))
                        start_date = self.add_months(start_date, 1, 'min')
                        last_date = start_date.replace(day=max(
                            start_date.day, calendar.monthrange(
                                start_date.year, start_date.month)[1]))
                        period_serial += 1
                    else:
                        create_period = False
            # for quarterly
            elif rec.appraisal_policy == 'quarterly':
                period_vals_list = self.get_appraisal_period(
                    current_month_sd, 2)
            # for Half Yearly
            elif rec.appraisal_policy == 'half_yearly':
                period_vals_list = self.get_appraisal_period(
                    current_month_sd, 5)
            # for Annually
            elif rec.appraisal_policy == 'annually':
                period_vals_list = self.get_appraisal_period(
                    current_month_sd, 11)
            rec.app_eval_ids = period_vals_list
            rec.state = 'in_progress'

    @api.multi
    def appraisal_configuration_done(self):
        """
        close all appraisal cycle
        :return:
        """
        for rec in self:
            for period_line_rec in rec.app_eval_ids:
                period_line_rec.state = 'done'
            rec.state = 'done'

    @api.multi
    def count_no_of_appraisal(self):
        self.no_of_appraisal = self.env['hr.employee.kra'].search_count(
            [('appraisal_template_id', '=', self.id),
             ('assessment_type', '=', 'self_assessment')])

    @api.multi
    def open_appraisal(self):
        tree_view_id = self.env.ref(
            'bista_hr_appraisal_evaluation.hr_employee_kra_self_asses_tree').id
        form_view_id = self.env.ref(
            'bista_hr_appraisal_evaluation.hr_employee_kra_form').id
        domain = [('assessment_type', '=', 'self_assessment'),
                  ('appraisal_template_id', '=', self.id)]
        return {
            'name': 'HR Review',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'view_id': tree_view_id,
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'res_model': 'hr.employee.kra',
            'domain': domain,
            'target': 'current',
        }

    # @api.onchange('start_date')
    # def _on_change_start_date(self):
    #     if self.start_date:
    #         self.end_date = datetime.datetime.strftime(
    #             datetime.datetime.strptime(self.start_date, DF).replace(
    #                 month=12, day=31), DF)


class HrAppraisalConfigurationPeriod(models.Model):
    _name = 'hr.appraisal.configuration.period'

    name = fields.Char(string='Name')
    date_start = fields.Date(string='Date Start')
    date_end = fields.Date(string='Date End')
    appraisal_template_id = fields.Many2one(
        'hr.appraisal.configuration', 'Appraisal Template', ondelete='cascade')

    state = fields.Selection([('in_progress', 'In progress'),
                              ('done', 'Closed')],
                             string="State", default='in_progress')
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)

    @api.multi
    def appraisal_configuration_close(self):
        self.write({'state': 'done'})
