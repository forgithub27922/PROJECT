# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _

import logging
# from collections import OrderedDict

_logger = logging.getLogger(__name__)


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    def disp_model_for_existing_location(self, barcode):
        product_id = self.env['product.product'].search([('barcode', '=', barcode)])
        stock_picking = self.env['stock.picking'].search([('product_id', '=', product_id.id)])

        lst_moves = []
        for rec in stock_picking:
            for rec_line in rec.move_line_ids:
                dict_moves = {'location_dest_id': rec_line.location_dest_id.with_context(lang=self.env.user.lang).name, 'qty_done': rec_line.qty_done}
                lst_moves.append(dict_moves)

        if lst_moves:
            return {'res': {'barcode': barcode, 'lst_moves': lst_moves}}
        else:
            return {'no_res': 'Record does not exist'}
