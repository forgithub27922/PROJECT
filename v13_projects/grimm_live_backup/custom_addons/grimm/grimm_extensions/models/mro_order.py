# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MROOrder(models.Model):
    _inherit = 'grimm.mro.order'

    @api.model
    def _get_default_analytic_account(self):
        context = dict(self._context or {})
        subscription_id = context.get('subscription_id', False)
        if subscription_id:
            subscription = self.env['sale.subscription'].browse(subscription_id)
            return subscription.analytic_account_id
        return False

    analytic_account_id = fields.Many2one(default=_get_default_analytic_account)
    task_id = fields.Many2one('project.task', string='Task')

    def create_task(self):
        for mro_order in self:
            if mro_order.task_id:
                continue

            assets = []
            for asset_order in mro_order.asset_order_ids:
                assets.append(asset_order.asset_id.id)

            vals = {
                'name': mro_order.name,
                'kanban_state': 'normal',
                'partner_id': mro_order.partner_id.id,
                'mro_order_id': mro_order.id,
                'asset_ids': [(6, 0, assets)]
            }
            task = self.env['project.task'].create(vals)
            mro_order.task_id = task

    def action_task(self):
        self.ensure_one()
        # task_id = []
        # for mro_order in self:
        #     task_id.extend(mro_order.task_id.id)

        form_view_id = self.env.ref('grimm_extensions.view_grimm_project_task_form_view_inherit').id
        result = {
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'views': [(form_view_id, 'form')],
            'res_id': self.task_id.id,
            # 'domain': ['id', '=', self.task_id.id],
            'context': {'create': False},
            'name': 'Task',
        }
        return result
