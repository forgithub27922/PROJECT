# -*- coding: utf-8 -*-


from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _compute_assets(self):
        for partner in self:
            counter = self.env['grimm.asset.asset'].search_count(
                [('partner_owner', '=', partner.id), ('active', '=', True)])
            partner.total_assets = counter

    def _get_history_count(self):
        for record in self:
            record.previous_assets_count = self.env['grimm.owner.history'].sudo().search_count(
                [('partner_id', '=', record.id), ('active', '=', False)])

    total_assets = fields.Integer(compute='_compute_assets')
    previous_assets_count = fields.Integer(string='Ex Assets', compute='_get_history_count')

    def action_asset_history(self):
        self.ensure_one()
        rec_ids = self.env['grimm.owner.history'].search(
            [('partner_id', '=', self.id), ('active', '=', False)], order='create_date desc')
        asset_ids = []
        for rec_id in rec_ids:
            asset_ids.append(rec_id.asset_id.id)

        list_view_id = self.env.ref('asset_base.view_grimm_asset_asset_tree').id
        form_view_id = self.env.ref('asset_base.view_grimm_asset_asset_form').id

        result = {
            "type": "ir.actions.act_window",
            "res_model": "grimm.asset.asset",
            "views": [[list_view_id, "tree"], [form_view_id, "form"]],
            "domain": [["id", "in", asset_ids]],
            "context": {"create": False},
            "name": "Assets",
        }
        if len(rec_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % asset_ids
        elif len(rec_ids) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = asset_ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result
