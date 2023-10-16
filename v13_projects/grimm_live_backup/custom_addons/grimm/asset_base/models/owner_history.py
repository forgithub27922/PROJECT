# -*- coding: utf-8 -*-


from odoo import models, api, fields, _


class OwnerHistory(models.Model):
    _name = 'grimm.owner.history'
    _description = 'Owner History'

    model_name = fields.Char('Model name')
    partner_id = fields.Many2one('res.partner', string='Owner', ondelete='restrict', index=True)
    record_id = fields.Integer('Record id')
    active = fields.Boolean('Is active?', copy=False, default=True)
    create_date = fields.Datetime(string='Creation Date', readonly=True,
                                  index=True, help="Date on which link is created.")

    @api.model
    def get_current_owner(self, model, record_id):
        if record_id > 0:
            row = self.search([('model_name', '=', model), ('record_id', '=', record_id), ('active', '=', True)])
            if row:
                return row.partner_id
        return False

    @api.model
    def change_owner(self, model, record_id, partner_id):
        if record_id.id > 0:
            self.search([('model_name', '=', model), ('record_id', '=', record_id.id),
                         ('active', '=', True)]).write({'active': False})
            self.create(
                {'partner_id': partner_id.id, 'record_id': record_id.id, 'model_name': model, 'active': True})

    @api.model
    def get_owner_history_action(self, model, record_id):
        rec_ids = self.search(
            [('record_id', '=', record_id), ('model_name', '=', model), ('active', '=', False)],
            order='create_date desc')
        partner_ids = []
        for rec_id in rec_ids:
            partner_ids.append(rec_id.partner_id.id)

        list_view_id = self.env.ref('base.view_partner_tree').id
        form_view_id = self.env.ref('base.view_partner_form').id

        result = {
            "type": "ir.actions.act_window",
            "res_model": "res.partner",
            "views": [[list_view_id, "tree"], [form_view_id, "form"]],
            "domain": [["id", "in", partner_ids]],
            "context": {"create": False},
            "name": "Contracts",
        }
        if len(rec_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % partner_ids
        elif len(rec_ids) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = partner_ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result
