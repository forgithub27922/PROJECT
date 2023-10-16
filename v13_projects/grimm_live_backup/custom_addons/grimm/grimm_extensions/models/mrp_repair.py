# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MrpRepair(models.Model):
    _inherit = 'repair.order'

    asset_id = fields.Many2one('grimm.asset.asset', string='Asset')
    claim_id = fields.Many2one('crm.claim', string='Claim')
    task_id = fields.Many2one('project.task', string='Task')

    @api.onchange('asset_id')
    def onchange_asset_id(self):
        if self.asset_id:
            product_id = self.env['product.product'].search(
                [('product_tmpl_id', '=', self.asset_id.product_id.id)], limit=1)
            self.product_id = product_id.id
        else:
            self.product_id = False

    def action_confirm(self):
        for repair in self:
            if repair.task_id:
                continue

            assets = []
            for asset_repair in repair.asset_id:
                assets.append(asset_repair.id)

            vals = {
                'name': repair.name,
                'kanban_state': 'normal',
                'partner_id': repair.partner_id.id,
                'mrp_repair_id': repair.id,
                'asset_ids': [(6, 0, assets)],
            }
            task = self.env['project.task'].create(vals)
            repair.task_id = task
            return super(MrpRepair, self).action_confirm()
