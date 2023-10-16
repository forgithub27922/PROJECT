# -*- coding: utf-8 -*-

from odoo import api, models, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def action_confirm(self):
        res = super(StockPicking, self).action_confirm()
        for picking in self:
            if picking.partner_id.default_block:
                raise UserError(
                    _('You cannot confirm a stock picking with a blocked partner! '))
        return res

    def do_new_transfer(self):
        res = super(StockPicking, self).do_new_transfer()
        for picking in self:
            if picking.partner_id.default_block:
                raise UserError(
                    _('You cannot confirm a stock picking with a blocked partner! '))
        return res
