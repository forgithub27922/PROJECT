# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Stock(models.Model):
    _inherit = 'stock.move.line'

    def _get_available_locations(self):
        for row in self:
            stock_picking = self.env['stock.picking'].search([('product_id', '=', row.product_id.id)])

            lst_moves = []
            for rec in stock_picking:
                for rec_line in rec.move_line_ids:
                    if rec_line.product_id.qty_available > 0.0 and rec_line.location_dest_id.usage == 'internal':
                        lst_moves.append(rec_line.location_dest_id.with_context(lang=self.env.user.lang).name)

            row.availability = ', '.join(list(set(lst_moves)))

    is_photo_done = fields.Boolean("Foto", related='product_id.is_photo_done', readonly=True)
    availability = fields.Char(string='Availability', compute=_get_available_locations)
