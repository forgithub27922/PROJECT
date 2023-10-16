from odoo import fields, models, api, _

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.onchange('contact_type')
    def onchange_contact_type(self):
        if self.contact_type == 'employee':
            return {'domain': {'picking_type_id': [('code', '=', ['internal'])]}}
        return {'domain': {'picking_type_id': []}}













