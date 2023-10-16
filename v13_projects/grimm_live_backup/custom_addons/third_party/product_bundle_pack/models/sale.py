# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
##############################################################################


from odoo import api, models, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import SUPERUSER_ID



class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    @api.onchange('product_id', 'product_uom_qty')
    def _onchange_product_id_check_availability(self):
        # res = super(SaleOrderLine, self)._onchange_product_id_check_availability()
        if self.product_id.is_pack:
            if self.product_id.type == 'product':
                warning_mess = {}
                for pack_product in self.product_id.pack_ids:
                    qty = self.product_uom_qty
                    if qty * pack_product.qty_uom > pack_product.product_id.virtual_available:
                        warning_mess = {
                                'title': _('Not enough inventory!'),
                                'message' : ('You plan to sell %s but you only have %s %s available, and the total quantity to sell is %s !' % (qty, pack_product.product_id.virtual_available, pack_product.product_id.name, qty * pack_product.qty_uom))
                                }
                        return {'warning': warning_mess}
        else:
            return {}

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        procurements = []
        for line in self:
            if line.order_id.state == 'sale' and line.state != 'sale':
                line.state = 'sale'
            if line.state != 'sale' or not line.product_id.type in ('consu','product'):
                continue
            qty = line._get_qty_procurement(previous_product_uom_qty)
            for move in line.move_ids.filtered(lambda r: r.state != 'cancel'):
                qty += move.product_qty
            if float_compare(qty, line.product_uom_qty, precision_digits=precision) >= 0:
                continue

            group_id = line._get_procurement_group()
            if not group_id:
                group_id = self.env['procurement.group'].create(line._prepare_procurement_group_vals())
                line.order_id.procurement_group_id = group_id
            else:
                # In case the procurement group is already created and the order was
                # cancelled, we need to update certain values of the group.
                updated_vals = {}
                if group_id.partner_id != line.order_id.partner_shipping_id:
                    updated_vals.update({'partner_id': line.order_id.partner_shipping_id.id})
                if group_id.move_type != line.order_id.picking_policy:
                    updated_vals.update({'move_type': line.order_id.picking_policy})
                if updated_vals:
                    group_id.write(updated_vals)
            if line.product_id.is_pack:
                for product in line.product_id.pack_ids:
                    values = line.with_context({'product':product})._prepare_procurement_values(group_id=group_id)
                    product_qty = values.get('product_qty') - qty


                    procurements.append(self.env['procurement.group'].Procurement(
                        product.product_id, product_qty, product.uom_id,
                        line.order_id.partner_shipping_id.property_stock_customer,
                        line.name, line.order_id.name, line.order_id.company_id, values))
            else:
                values = line._prepare_procurement_values(group_id=group_id)
                product_qty = line.product_uom_qty - qty
                line_uom = line.product_uom
                quant_uom = line.product_id.uom_id
                product_qty, procurement_uom = line_uom._adjust_uom_quantities(product_qty, quant_uom)

                procurements.append(self.env['procurement.group'].Procurement(
                    line.product_id, product_qty, procurement_uom,
                    line.order_id.partner_shipping_id.property_stock_customer,
                    line.name, line.order_id.name, line.order_id.company_id, values))
        if procurements:
            self.env['procurement.group'].run(procurements)
        return True

    def _prepare_procurement_values(self, group_id):
        res = super(SaleOrderLine, self)._prepare_procurement_values(group_id=group_id)
        values = []
        date_planned = self.order_id.date_order + timedelta(days=self.customer_lead or 0.0) - timedelta(days=self.order_id.company_id.security_lead)
        if self.product_id.is_pack and self.product_id.pack_ids:
            prod = self._context.get('product')
            res.update({
                'name': prod.product_id.name,
                'origin': self.order_id.name,
                'date_planned': date_planned.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                'product_id': prod.product_id.id,
                'product_qty': prod.qty_uom * self.product_uom_qty,
                'product_uom': prod.uom_id and prod.uom_id.id,
                'company_id': self.order_id.company_id,  # .id,
                'group_id': group_id,
                'sale_line_id': self.id,
                'warehouse_id': self.order_id.warehouse_id and self.order_id.warehouse_id,
                'location_id': self.order_id.partner_shipping_id.property_stock_customer.id,
                'route_ids': self.route_id,
                # and [(4, self.route_id.id)] or [], Commented code to resolve third party module error.
                'partner_dest_id': self.order_id.partner_shipping_id,
                # and self.order_id.partner_shipping_id.id, #Commented code to resolve third party module error. OD-806
            })
        else:
            res.update({
            'company_id': self.order_id.company_id,
            'group_id': group_id,
            'sale_line_id': self.id,
            'date_planned': date_planned.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            'route_ids': self.route_id,
            'warehouse_id': self.order_id.warehouse_id or False,
            'partner_dest_id': self.order_id.partner_shipping_id
        })    
        return res

    def _get_delivered_qty(self):
        self.ensure_one()
        order = super(SaleOrderLine, self)._get_delivered_qty()
        picking_ids = self.env['stock.picking'].search([('origin','=',self.order_id.name)])
        list_of_picking = []
        list_of_pack_product = []
        for pic in picking_ids:
            list_of_picking.append(pic.id)
        if len(picking_ids) >= 1:
            if self.product_id.is_pack:
                for pack_item in self.product_id.pack_ids:
                    list_of_pack_product.append(pack_item.product_id.id)
                stock_move_ids = self.env['stock.move'].search([('product_id','in',list_of_pack_product),('picking_id','in',list_of_picking)])
                pack_delivered = all([move.state == 'done' for move in stock_move_ids])
                if pack_delivered:
                    return self.product_uom_qty
                else:
                    return 0.0
        return order


class ProcurementRule(models.Model):
    _inherit = 'stock.rule'
    
    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, values, group_id):
        result = super(ProcurementRule, self)._get_stock_move_values(product_id, product_qty, product_uom, location_id, name, origin, values, group_id)
        
        if  product_id.pack_ids:
            for item in product_id.pack_ids:
                result.update({
                    'product_id': item.product_id.id,
                    'product_uom': item.uom_id and item.uom_id.id,
                    # 'product_uom_qty': item.qty_uom,
                    'origin': origin,
                    })
        return result
