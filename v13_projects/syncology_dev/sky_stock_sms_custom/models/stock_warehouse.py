from odoo import fields, models, api, _


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    addr_comp_id = fields.Many2one('res.company', 'Address')