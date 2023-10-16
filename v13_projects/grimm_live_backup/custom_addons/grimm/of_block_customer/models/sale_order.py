# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _compute_block(self):
        for this in self:
            this.block_id = this.partner_id.parent_id.default_block or this.partner_id.default_block

    block_id = fields.Many2one(
        comodel_name='sale.block.reason',
        string='Block Reason', readonly=True, compute='_compute_block')

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """Add the 'Default Delivery Block Reason' if set in the partner."""
        res = super(SaleOrder, self).onchange_partner_id()
        for so in self:
            so.block_id = so.partner_id.default_block or \
                          False
        return res

    def action_remove_block(self):
        """Remove the delivery block and create procurements as usual."""
        self.write({'block_id': False})
        for order in self:
            order.order_line._action_procurement_create()

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        new_so = super(SaleOrder, self).copy(default=default)
        for so in new_so:
            if (so.partner_id.default_block and not
            so.block_id):
                so.block_id = so.partner_id.default_block
        return new_so

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            if order.block_id:
                raise UserError(_('You cannot confirm a sale order with a blocked partner! '))
        return res
