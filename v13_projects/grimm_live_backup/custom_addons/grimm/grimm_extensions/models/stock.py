# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    sale_purchase_links = fields.One2many('grimm.sale.purchase.link', 'picking_id', string='Serial No.')
    claim_id = fields.Many2one('crm.claim', string='Claim')

#
# class StockPackOperation(models.Model):
#     _inherit = 'stock.pack.operation'
#
#     date_done = fields.Date(string='Delivery Date', copy=False)


class StockQuant(models.Model):
    _inherit = 'stock.move.line'

    @api.depends('product_id')
    def _get_warehouse(self):
        for rec in self:
            try:
                rec.storage_bin = ', '.join(rec.product_id.stock_quant_ids.filtered(lambda x: x.quantity > 0 and x.company_id).mapped(
                    lambda r: r.location_id.location_id.name + '/' + r.location_id.name if r.location_id.location_id else r.location_id.name))
            except:
                rec.storage_bin = ''

    storage_bin = fields.Char('Storage Bin', compute='_get_warehouse')
    picking_type_code = fields.Selection('Picking Type Code', related='picking_id.picking_type_code')
