# -*- coding: utf-8 -*-


from odoo import models, fields, api, _


class AssetFacility(models.Model):
    _name = 'grimm.asset.facility'
    _description = 'Asset Facility'

    def _get_history_count(self):
        for record in self:
            record.previous_owners_count = self.env['grimm.owner.history'].sudo().search_count(
                [('record_id', '=', record.id), ('active', '=', False), ('model_name', '=', 'grimm.asset.facility')])

    def _get_assets_count(self):
        for record in self:
            record.asset_ids_count = self.env['grimm.asset.asset'].search_count(
                [('asset_facility_id', '=', record.id)])

    asset_ids = fields.One2many('grimm.asset.asset', 'asset_facility_id', 'Assets')
    previous_owners_count = fields.Integer(string='Ex Owners', compute=_get_history_count)
    asset_ids_count = fields.Integer(string='Assets', compute=_get_assets_count)

    name = fields.Char(string='Name', required=True)
    partner_owner = fields.Many2one('res.partner', string='Owner', track_visibility='onchange')
    partner_contact = fields.Many2one('res.partner', string='Contact', track_visibility='onchange')
    partner_invoice = fields.Many2one('res.partner', string='Invoice', track_visibility='onchange')
    partner_delivery = fields.Many2one(
        'res.partner', string='Delivery', track_visibility='onchange')
    beneficiary = fields.Many2one('res.partner', 'Beneficiary', track_visibility='onchange')

    def update_contact_addresses(self, vals, propagate):
        self.write(vals)
        if propagate:
            for record in self:
                record.asset_ids.update_contact_addresses(vals, propagate)
        for record in self:
            current_owner = self.env['grimm.owner.history'].get_current_owner(
                'grimm.asset.facility', record.id)
            if record.partner_owner != current_owner:
                self.env['grimm.owner.history'].change_owner(
                    'grimm.asset.facility', record, record.partner_owner)

    def action_partner_history(self):
        self.ensure_one()
        return self.env['grimm.owner.history'].get_owner_history_action('grimm.asset.facility', self.id)

    def action_show_assets(self):
        ctx = self._context.copy()
        # TODO for what is this variable form_view_id?
        form_view_id = self.env.ref('asset_base.view_grimm_asset_kanban')
        result = {
            'name': _('Assets'),
            'type': 'ir.actions.act_window',
            'view_type': 'kanban',
            'view_mode': 'kanban,tree',
            'res_model': 'grimm.asset.asset',
            'target': 'current',
            'domain': [('partner_owner', '=', self.partner_owner.id)],
            'context': ctx,

        }
        return result
