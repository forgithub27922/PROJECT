# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class HrCompoffGiven(models.TransientModel):
    _name = 'hr.compoff.given'

    holiday_status_id = fields.Many2one("hr.holidays.status",
                                        string="Type", required=True)
    days = fields.Float('No. of Days')

    @api.multi
    def action_allocate_compoff(self):
        context = self._context
        holidays_obj = self.env['hr.holidays']
        active_rec = self.env['hr.compoff'].browse(context.get('active_id'))
        for rec in self:
            if rec.days <= 0:
                raise ValidationError(_('No. of days must be grater than '
                                        'zero.'))
            department_id = \
                active_rec.employee_id.department_id \
                and active_rec.employee_id.department_id.id \
                or False
            holidays_vals = {'name': active_rec.name,
                             'mode': 'employee',
                             'holiday_status_id':
                                 rec.holiday_status_id and
                                 rec.holiday_status_id.id or False,
                             'employee_id':
                                 active_rec.employee_id and
                                 active_rec.employee_id.id or False,
                             'date_from': active_rec.date_compoff,
                             'date_to': active_rec.date_compoff,
                             'number_of_days_temp': rec.days,
                             'department_id': department_id,
                             'type': 'add',
                             'notes': active_rec.notes or '',
                             'state': 'confirm',
                             'compoff_id': active_rec.id,
                             'compoff_date_expired': active_rec.date_expired,
                             }
            allocate_record = holidays_obj.create(holidays_vals)
            allocate_record.action_approve()
            if rec.holiday_status_id.double_validation:
                allocate_record.action_validate()
        return active_rec.write({'state': 'compoff_given'})
