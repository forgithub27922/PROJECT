# -*- encoding: utf-8 -*-
##########################################################################################
#
#    Copyright (C) 2019 Skyscend Business Solutions (https://www.skyscendbs.com)
#    Copyright (C) 2020 Skyscend Business Solutions Pvt. Ltd. (https://www.skyscendbs.com)
#
##########################################################################################
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Picking(models.Model):
    _name = "stock.picking"
    _inherit = ['stock.picking', 'barcodes.barcode_events_mixin']

    def on_barcode_scanned(self, barcode):
        """
        This method is used to process the scanned barcode.
        It will create a new line with the product matching the barcode.
        If the line is already existing, it will update the quantity for that product.
        ------------------------------------------------------------------------------
        @param barcode: The scanned barcode
        """
        prod_obj = self.env['product.product']
        product = prod_obj.search([('barcode', '=', barcode)], limit=1)
        if product:
            for order in self:
                if order.state in ['done', 'cancel']:
                    raise ValidationError(_('The Picking %s is already %s.') % (
                        order.name, dict(order._fields['state'].selection).get(order.state)))
                if order.show_operations:
                    if order.picking_type_code == "incoming":
                        order.move_without_package_update(order, product)
                    else:
                        order.move_line_without_package_update(order, product)
                else:
                    order.move_without_package_update(order, product)
        else:
            raise ValidationError(_("Barcode is Invalid !!!"))

    def move_line_without_package_update(self, order, product):
        """
        This method is used to process the update move line.
        ------------------------------------------------------------------------------
        @param barcode: The scanned barcode
        """
        stock_line = order.move_line_ids_without_package.filtered(lambda r: r.product_id.id == product.id)
        if len(stock_line) > 0:
            stock_line = stock_line[0]
            stock_line.qty_done = stock_line.qty_done + 1
        else:
            if product:
                stock_line_vals = {
                    'product_id': product.id,
                    'product_uom_id': product.uom_po_id.id,
                    'location_id': order.location_id.id,
                    'location_dest_id': order.location_dest_id.id,
                    'qty_done': 1,
                }
                order.move_line_ids_without_package = [(0, 0, stock_line_vals)]

    def move_without_package_update(self, order, product):
        """
        This method is used to process the update move line.
        ------------------------------------------------------------------------------
        @param barcode: The scanned barcode
        """
        stock_line = order.move_ids_without_package.filtered(lambda r: r.product_id.id == product.id)
        if len(stock_line) > 0:
            stock_line = stock_line[0]
            stock_line.quantity_done = stock_line.quantity_done + 1
            stock_line.product_uom_qty = stock_line.product_uom_qty + 1
        else:
            if product:
                stock_line_vals = {
                    'product_id': product.id,
                    'description_picking': product.name,
                    'name': product.name,
                    'location_id': order.location_id.id,
                    'location_dest_id': order.location_dest_id.id,
                    'product_uom': product.uom_po_id.id,
                    'quantity_done': 1,
                    'product_uom_qty': 1,
                }
                order.move_ids_without_package = [(0, 0, stock_line_vals)]
