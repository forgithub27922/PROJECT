# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from dateutil.relativedelta import relativedelta
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class HrCompoff(models.Model):
    _name = 'hr.compoff'
    _inherit = ['mail.thread']
    _description = 'Comp-Off'
    _order = "date_compoff desc"

    def _default_employee(self):
        return self.env['hr.employee'].search([
            ('user_id', '=', self.env.uid)], limit=1)

    @api.one
    @api.depends('date_compoff')
    def _get_expired_date(self):
        holiday_type_obj = self.env['hr.holidays.status']
        compoff_ids = holiday_type_obj.search([
            ('allow_compoff', '=', True)], limit=1)
        expired_days = 0
        if compoff_ids:
            expired_days = compoff_ids.expired_days
        expired_date = \
            datetime.strptime(self.date_compoff, DEFAULT_SERVER_DATE_FORMAT
                              ) + relativedelta(days=expired_days)
        self.date_expired = expired_date

    @api.one
    @api.depends('date_compoff')
    def _get_attendance(self):
        analytic_line_obj = self.env['account.analytic.line']
        analytic_line_ids = analytic_line_obj.sudo().search(
            [('employee_id', '=', self.employee_id.id),
             ('date', '=', self.date_compoff)])
        self.attendance = sum(line.unit_amount for line in analytic_line_ids)

    @api.multi
    def _get_allocation_count(self):
        holidays_obj = self.env['hr.holidays']
        for rec in self:
            holiday_ids = holidays_obj.search([('compoff_id', '=', rec.id)])
            rec.allocation_count = len(holiday_ids)

    name = fields.Char('Description', states={'draft': [('readonly', False)]},
                       readonly=True, required=True,
                       track_visibility='onchange')
    date_compoff = fields.Date('Date', default=fields.Date.today,
                               states={'draft': [('readonly', False)]},
                               readonly=True, copy=False, required=True,
                               track_visibility='onchange')
    employee_id = fields.Many2one('hr.employee', 'Employee',
                                  default=_default_employee,
                                  states={'draft': [('readonly', False)]},
                                  readonly=True, copy=False, required=True,
                                  track_visibility='onchange')
    parent_id = fields.Many2one('hr.employee', 'Manager', required=True)
    attendance = fields.Float(compute='_get_attendance', string='Attendance')
    state = fields.Selection([('draft', 'Draft'),
                              ('submit', 'To Submit'),
                              ('approve_manager', 'Approved by Manager'),
                              ('approve_hr', 'Approved by HR'),
                              ('compoff_given', 'Compoff Given'),
                              ('refused', 'Refused')],
                             string='State', default='draft',
                             states={'draft': [('readonly', False)]},
                             readonly=True, copy=False,
                             track_visibility='always')
    notes = fields.Text('Comments')
    date_expired = fields.Date(compute='_get_expired_date',
                               string='Valid Till', readonly=True,
                               copy=False)
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True,
                                 default=lambda self: self.env.user.company_id)
    user_id = fields.Many2one('res.users', string='User',
                              default=lambda self: self.env.user)
    allocation_count = fields.Integer(string='# of Allocation',
                                      compute='_get_allocation_count',
                                      readonly=True)

    @api.multi
    def action_view_allocation(self):
        self.ensure_one()
        holidays_obj = self.env['hr.holidays']
        holiday_ids = holidays_obj.search([('compoff_id', '=', self.id)])
        action = self.env.ref('hr_holidays.open_allocation_holidays').read()[0]
        if len(holiday_ids) > 1:
            action['domain'] = [('id', 'in', holiday_ids.ids)]
        elif len(holiday_ids) == 1:
            action['views'] = [
                (self.env.ref('hr_holidays.edit_holiday_new').id, 'form')]
            action['res_id'] = holiday_ids.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.onchange('employee_id')
    def onchange_employee(self):
        if self.employee_id:
            sudo_emp = self.employee_id.sudo()
            if not sudo_emp.parent_id:
                msg = 'Please contact to Administrator for set your manager.'
                raise ValidationError(_(msg))
            if sudo_emp.parent_id:
                self.parent_id = sudo_emp.parent_id.id or False

    @api.multi
    def action_submit(self):
        return self.write({'state': 'submit'})

    @api.multi
    def action_approve_manager(self):
        is_manager = self.env.user. \
            has_group('hr_holidays.group_hr_holidays_manager')
        is_officer = self.env.user. \
            has_group('hr_holidays.group_hr_holidays_user')
        admin = self.env.ref('base.user_root').ids
        for rec in self:
            is_allow = False
            user_id = \
                self.employee_id.user_id \
                and self.employee_id.user_id.id or False
            if self._uid == admin or is_manager:
                is_allow = True
            elif not is_officer \
                    or (user_id and user_id == self._uid):
                raise ValidationError(_('You can not approved your Comp-Off.'))
            rec.write({'state': 'approve_manager'})
        return True

    @api.multi
    def action_approve_hr(self):
        return self.write({'state': 'approve_hr'})

    @api.multi
    def action_compoff_given(self):
        ctx = dict(self._context)
        holiday_type_obj = self.env['hr.holidays.status']
        holiday_type_ids = holiday_type_obj.search(
            [('allow_compoff', '=', True)], limit=1)
        if not holiday_type_ids:
            raise ValidationError(
                _('Atleast one leave type should be Comp-off.\n'
                  'Menu: Leaves > Configuration'))
        ctx.update({'default_holiday_status_id': holiday_type_ids.id})
        view = self.env.ref('bista_hr_compoff.view_hr_compoff_given_form')
        return {
            'name': _('Given Comp-Off'),
            'context': ctx,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hr.compoff.given',
            'views': [(view.id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    @api.multi
    def action_refused(self):
        return self.write({'state': 'refused'})
