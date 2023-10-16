import time
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    status = fields.Selection([('joined', 'Joined'),
                               ('training', 'Training'),
                               ('ex-training', 'Extended Training'),
                               ('probation', 'Probation'),
                               ('ex-probation', 'Extended Probation'),
                               ('employment', 'Employment'),
                               ('pip', 'PIP'),
                               ('notice_period', 'Notice Period'),
                               ('relieved', 'Relieved'),
                               ('terminated', 'Terminated'),
                               ('rejoined', 'Rejoined')],
                              string='Status', default='joined')
    status_history = fields.One2many('hr.emp.status.history', 'emp_id',
                                     string='Status History')
    is_training = fields.Boolean('ITraining')
    is_ex_training = fields.Boolean('Extend Training')
    is_probation = fields.Boolean('Probation')
    is_ex_probation = fields.Boolean('Extend Probation')
    is_employment = fields.Boolean('Employment')
    is_pip = fields.Boolean('Pip', help='Performanace improvement program')
    is_notice_period = fields.Boolean('Notice Period')
    is_relieved = fields.Boolean('Relieved')
    is_rejoined = fields.Boolean('Rejoined')
    is_terminated = fields.Boolean('Terminated')

    @api.model
    def create(self, vals):
        result = super(HrEmployee, self).create(vals)
        if not vals.get('date_joining'):
            doj = datetime.now().date()
            result.date_joining = doj
            result.status_history = [(0, 0, {'state': 'joined',
                                             'start_date': doj,
                                                # 'end_date': joining_date
                                                })]
        else:
            result.status_history = [(0, 0, {'state': 'joined',
                                             'start_date': vals.get('date_joining'),
                                                })]
        return result

    @api.multi
    def write(self, vals):
        if self._context.get('from_emp_history'):
            return super(HrEmployee, self).write(vals)
        res = super(HrEmployee, self).write(vals)
        if vals.get('date_joining', False):
            for rec in self:
                for history in rec.status_history:
                    if history.state == 'joined':
                        history.start_date = vals.get('date_joining')
                        # history.end_date = vals.get('date_joining')
        return res

    @api.multi
    def open_wizard(self):
        state_list = ['training', 'probation', 'ex-training', 'ex-probation',
                      'employment', 'pip', 'notice_period', 'relieved',
                      'terminated', 'rejoined']
        ctx = self._context.copy()
        for state in state_list:
            if ctx.get(state):
                ctx.update({'default_status': state})
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hr.lifecycle.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': ctx,
        }

    @api.model
    def pre_employee_status_update(self):
        employees = self.search([])
        for emp in employees:
            date_result = fields.date.today()
            if emp.date_joining:
                date_result = emp.date_joining
            joined_history = emp.status_history.filtered(lambda x:
                                                         x.state != 'joined')
            if not joined_history:
                vals = {'emp_id': emp.id,
                        'state': 'joined',
                        'start_date': date_result,
                        'end_date': date_result,
                        'company_id': emp.company_id and emp.company_id.id or
                                      False
                        }
                emp.write({'status_history': [(0, 0, vals)]})


class HrEmployeeStatusHistory(models.Model):
    _name = 'hr.emp.status.history'
    _description = "Employee Status History"
    _order = 'start_date desc'

    emp_id = fields.Many2one('hr.employee', string='Employee')
    state = fields.Selection([('joined', 'Joined'), ('training', 'Training'),
                              ('ex-training', 'Extended Training'),
                              ('probation', 'Probation'),
                              ('ex-probation', 'Extended Probation'),
                              ('employment', 'Employment'), ('pip', 'PIP'),
                              ('notice_period', 'Notice Period'),
                              ('relieved', 'Relieved'),
                              ('rejoined', 'Rejoined'),
                              ('terminated', 'Terminated')],
                             string='State')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    is_emp = fields.Boolean('Employment')
    is_np = fields.Boolean('Notice')
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env.user.company_id)

    @api.constrains('start_date', 'end_date')
    def check_in_out_dates(self):
        """
            End date date should be greater than the start date.
        """
        for rec in self:
            if rec.end_date and rec.start_date and rec.end_date < rec.start_date:
                raise ValidationError(_('End Date should be greater \
                    than Start Date in Employee Life Cycle'))

    @api.multi
    def write(self, vals):
        res = super(HrEmployeeStatusHistory, self).write(vals)
        if self.state == 'joined':
            self.emp_id.with_context({'from_emp_history':True}).\
            write({'date_joining': vals.get('start_date')})
        return res
