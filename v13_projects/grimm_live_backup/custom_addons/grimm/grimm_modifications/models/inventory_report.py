# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class InventoryReport(models.Model):
    _name = "inventory.development.report"
    _description = 'Inventory development report'
    _order = "date desc"

    date = fields.Date(string='Date')
    location_id = fields.Many2one('stock.location', string='Location')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    total_qty = fields.Float('Total Qty')
    currency_id = fields.Many2one('res.currency', string='Currency')
    total_value = fields.Monetary(string='Total Value')

    @api.model
    def create_inventory_development_rows(self):
        stock_location = self.env['stock.location'].search([('usage', '=', 'internal')], limit=100)
        for location in stock_location:
            stock_quant = self.env['stock.quant'].search([('location_id', 'child_of', location.id)])
            total_qty = 0
            total_val = 0
            for stack_qnt in stock_quant:
                # Fetching calculated_standard_price from product_id leads to key error, temporary fix is by indexing product_id by 0
                total_qty += stack_qnt.quantity
                total_val += stack_qnt.quantity * stack_qnt.product_id[0].calculated_standard_price

            vals = {
                'date': datetime.now(),
                'location_id': location.id,
                'warehouse_id': stock_quant[0].product_id[0].warehouse_id.id if stock_quant else False,
                'total_qty': total_qty,
                'total_value': total_val
            }

            self.create(vals)
