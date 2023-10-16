# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models
from odoo.addons.bista_hijri_date.models.hijri import Convert_Date
from datetime import datetime


class HrTerminationRequest(models.Model):
    _inherit = 'hr.termination.request'

    state = fields.Selection([('draft', 'Draft'),
                              ('submit', 'Submit'),
                              ('notice', 'Notice Period'),
                              ('exit_interview', 'Exit Interview'),
                              ('approve_hr', 'Approve by HR'),
                              ('no_dues', 'No Dues'),
                              ('retained', 'Retained'),
                              ('released', 'Released')],
                             default='draft',
                             track_visibility='onchange')
    exit_interview_id = fields.Many2one(
        'exit.interview', string="Exit Interview")

    @api.multi
    def state_arrange_exit_interview(self):
        """
        Set request state to exit interview and create record of ext interview
        :return: Form view of exit interview in current window.
        """
        for rec in self:
            rec.state = 'exit_interview'
            record = self.env['exit.interview'].create(
                {'name': "Exit Interview of %s" % (rec.employee_id.name),
                 'employee_id': rec.employee_id.id,
                 'department_id': rec.department_id.id,
                 'manager_id': rec.manager_id.id,
                 'job_id': rec.employee_id.job_id.id,
                 'date': datetime.now().date(),
                 'date_hijri': Convert_Date(
                     datetime.now().date(), 'english', 'islamic'),
                 'reason': rec.reason
                 })
            rec.exit_interview_id = record.id
            rec.send_intimation('bista_eos.termination_req_approval_template')
        return {
            'name': 'Exit Interview',
            'type': 'ir.actions.act_window',
            'res_id': record.id or False,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'exit.interview',
            'target': 'current',
        }