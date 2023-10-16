# -*- coding: utf-8 -*-

from odoo import models, api, fields


class DelegateTaskWizard(models.TransientModel):
    _name = 'delegate.task.wizard'
    _description = 'Delegate task wizard'

    task_id = fields.Many2one('project.task', string='Task', readonly=True)
    task_user = fields.Many2one('res.users', string='Neuer Verantwortlicher')

    def delegate_task(self):
        self.ensure_one()
        context = dict(self._context or {})
        print(context)
        active_ids = context.get('active_ids', [])
        task = self.env['project.task'].browse(active_ids)
        task.write({'user_id': self.task_user.id})
        return {'type': 'ir.actions.act_window_close'}
