# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _get_related_so(self):
        for record in self:
            sale_order = self.env['sale.order'].search(
                [('name', '=', record.origin)], limit=1)
            record.sale_order_id = sale_order.id if sale_order else False

    sale_order_id = fields.Many2one('sale.order', 'Sale Order', compute=_get_related_so)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    parent_partner_print = fields.Boolean(string='External Address', default=False)
