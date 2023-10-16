from odoo import models, fields, api, _
from odoo.exceptions import UserError


class MergePicking(models.TransientModel):
    _name = 'merge.picking.order.wiz'
    _description = 'Merge the picking order'

    merge_type = fields.Selection(selection=[('new_order_state_cancel',
                                              'New Picking orders and Cancel Selected orders.'),
                                             ('new_order_delete_order',
                                              'New Picking orders and Delete all selected orders'),
                                             ('select_exist_order_state_cancel',
                                              'Merge Picking orders on existing selected orders and cancel others.'),
                                             ('select_exist_order_delete_order',
                                              'Merge Picking orders on existing selected orders and delete others.')],
                                  string='merge_type', default='new_order_state_cancel')

    merge_picking_order_id = fields.Many2one('stock.picking', 'Picking Order')

    @api.onchange('merge_type')
    def on_change_picking_orders(self):
        """
        This method will help to show the many2one field and show the selected picking orders
        :return: res
        @:param self:object pointer
        """
        lst = []
        picking_order_dict = {}
        picking_orders = self.env['stock.picking'].browse(self._context.get('active_ids', []))
        for pick_orders in picking_orders:
            lst.append(pick_orders.id)
        picking_order_dict['domain'] = {
            'merge_picking_order_id': [('id', 'in', lst)]
        }
        return picking_order_dict

    def merge_picking_orders(self):
        """
        This Method will help to merge the picking orders
        @:param: self:object pointer
        """
        picking_orders = self.env['stock.picking'].browse(self._context.get('active_ids', []))
        print("\n\n\n :::::> PICKING ORDERS", picking_orders)

        # check the length of selected orders
        if len(self._context.get('active_ids', [])) < 2:
            raise UserError(_('Please select at least two picking orders to perform the Merge Operation.'))

        # check the state of selected orders
        # for order in picking_orders:
        if any(order.state != 'draft' for order in picking_orders):
            raise UserError(
                _('Please select those picking orders which are in Draft state to perform the Merge Operation.'))

        # check the customer of selected orders
        first_picking_order = picking_orders[0]
        print("\n\n\n ::::::::> FIRST CUSTOMER", first_picking_order)
        for customer in picking_orders:
            if customer.partner_id != first_picking_order.partner_id:
                print("\n\n\n :::::::> CUSTOMER ID", customer.partner_id)
                print("\n\n\n :::::::> FIRST PICKING CUSTOMER ID", first_picking_order.partner_id)
                raise UserError(_('Please select same name picking orders to perform the merge operation.'))

        # check the orders operation type
        operation_type = first_picking_order
        print("\n\n\n ::::::>OPERATION TYPE", operation_type)
        for op_type in picking_orders:
            if op_type.picking_type_id != operation_type.picking_type_id:
                raise UserError(
                    _('Please select those record which operation type are same to perform the merge operation.'))

        # Merge The Picking Orders
        # option-1 New Picking orders and Cancel Selected orders.
        if self.merge_type == 'new_order_state_cancel':
            operation_type_obj = self.env['stock.picking.type'].search([])
            loc = first_picking_order.location_id
            print("\n\n\n ::::::> LOC", loc)
            picking_order_obj = self.env['stock.picking']
            print("\n\n\n :::::::> PICKING ORDERS OBJ", picking_order_obj)
            picking_product_lst = []
            picking_order_id_if_exist = True
            for order in picking_orders:
                for line in order.move_ids_without_package:
                    print("\n\n\n :::::::::>LINE", line)
                    for order_dict in picking_product_lst:
                        print("\n\n\n :::::::> ORDER DICT", order_dict)
                        if order_dict[2].get('product_id') == line.product_id.id:
                            qty = order_dict[2].get('product_uom_qty')
                            order_dict[2].update({
                                'product_uom_qty': qty + line.product_uom_qty
                            })
                            print("\n\n\n::::::> FINAL DICT", order_dict)
                            picking_order_id_if_exist = False
                    if picking_order_id_if_exist:
                        picking_product_lst.append((0, 0, {
                            'name': line.name,
                            'product_id': line.product_id.id,
                            'product_uom_qty': line.product_uom_qty,
                            'product_uom': line.product_uom
                        }))
            for o_type in operation_type_obj:
                print("\n\n\n::::> OPERATION TYPES", o_type)
                if o_type.name == 'Receipts':
                    print("\n\n\n :::::::> OPERATION TYPE", o_type.name)
                    picking_order_vals = {
                        'partner_id': first_picking_order.partner_id.id,
                        'picking_type_id': first_picking_order.picking_type_id.id,
                        'location_id': first_picking_order.location_id.id,
                        'location_dest_id': first_picking_order.location_dest_id.id,
                        'move_ids_without_package': picking_product_lst
                    }
                    data = picking_order_obj.create(picking_order_vals)
                    print("\n\n\n :::::::> DATA", data)
                for picking_selected_orders in picking_orders:
                    picking_selected_orders.state = 'cancel'

        # option-2 New Picking orders and Delete all selected orders.
        elif self.merge_type == 'new_order_delete_order':
            operation_type_obj = self.env['stock.picking.type'].search([])
            loc = first_picking_order.location_id
            print("\n\n\n ::::::> LOC", loc)
            picking_order_obj = self.env['stock.picking']
            print("\n\n\n :::::::> PICKING ORDERS OBJ", picking_order_obj)
            picking_product_lst = []
            picking_order_id_if_exist = True
            for order in picking_orders:
                for line in order.move_ids_without_package:
                    print("\n\n\n :::::::::>LINE", line)
                    for order_dict in picking_product_lst:
                        print("\n\n\n :::::::> ORDER DICT", order_dict)
                        if order_dict[2].get('product_id') == line.product_id.id:
                            qty = order_dict[2].get('product_uom_qty')
                            order_dict[2].update({
                                'product_uom_qty': qty + line.product_uom_qty
                            })
                            print("\n\n\n::::::> FINAL DICT", order_dict)
                            picking_order_id_if_exist = False
                    if picking_order_id_if_exist:
                        picking_product_lst.append((0, 0, {
                            'name': line.name,
                            'product_id': line.product_id.id,
                            'product_uom_qty': line.product_uom_qty,
                            'product_uom': line.product_uom
                        }))
            for o_type in operation_type_obj:
                print("\n\n\n::::> OPERATION TYPES", o_type)
                if o_type.name == 'Receipts':
                    print("\n\n\n :::::::> OPERATION TYPE", o_type.name)
                    picking_order_vals = {
                        'partner_id': first_picking_order.partner_id.id,
                        'picking_type_id': first_picking_order.picking_type_id.id,
                        'location_id': first_picking_order.location_id.id,
                        'location_dest_id': first_picking_order.location_dest_id.id,
                        'move_ids_without_package': picking_product_lst
                    }
                    data = picking_order_obj.create(picking_order_vals)
                    print("\n\n\n :::::::> DATA", data)

            for picking_selected_orders in picking_orders:
                print("\n\n\n ::::> PK!L112222", picking_selected_orders)
                picking_selected_orders[0].unlink()

        # option-3 : Merge Picking orders on existing selected orders and cancel others
        elif self.merge_type == 'select_exist_order_state_cancel':
            print('\n\n\nMERGE TYPE++++++++++++++++++', self.merge_type)
            selected_picking_order = self.merge_picking_order_id

            so_not_exist = True
            oder_line_rec = []
            picking_order_vals = {
                'partner_id': selected_picking_order.partner_id.id,
                'picking_type_id': selected_picking_order.picking_type_id.id,
                'location_id': selected_picking_order.location_id.id,
                'location_dest_id': selected_picking_order.location_dest_id.id,
                'move_ids_without_package': oder_line_rec
            }
            for product in picking_orders:

                if product.id != selected_picking_order.id:
                    for line in product.move_ids_without_package:
                        for fst_line in selected_picking_order.move_ids_without_package:
                            if fst_line.product_id.id == line.product_id.id:
                                qty = fst_line.product_uom_qty
                                fst_line.product_uom_qty = qty + line.product_uom_qty
                                so_not_exist = False

                        if so_not_exist:
                            oder_line_rec.append(
                                (0, 0, {'product_id': line.product_id.id,
                                        'product_uom_qty': line.product_uom_qty,
                                        'name': line.name,
                                        'product_uom': line.product_uom,
                                        'location_id': selected_picking_order.location_id.id,
                                        'location_dest_id': selected_picking_order.location_dest_id.id,
                                        }))

            selected_picking_order.write(picking_order_vals)

            for picking_selected_orders in picking_orders:
                if picking_selected_orders.id != selected_picking_order.id:
                    picking_selected_orders.state = 'cancel'


        # option-4 : Merge Picking orders on existing selected orders and delete others
        else:
            print('\n\n\nMERGE TYPE++++++++++++++++++', self.merge_type)
            selected_picking_order = self.merge_picking_order_id

            so_not_exist = True
            oder_line_rec = []
            picking_order_vals = {
                'partner_id': selected_picking_order.partner_id.id,
                'picking_type_id': selected_picking_order.picking_type_id.id,
                'location_id': selected_picking_order.location_id.id,
                'location_dest_id': selected_picking_order.location_dest_id.id,
                'move_ids_without_package': oder_line_rec
            }
            for product in picking_orders:

                if product.id != selected_picking_order.id:
                    for line in product.move_ids_without_package:
                        for fst_line in selected_picking_order.move_ids_without_package:
                            if fst_line.product_id.id == line.product_id.id:
                                qty = fst_line.product_uom_qty
                                fst_line.product_uom_qty = qty + line.product_uom_qty
                                so_not_exist = False

                        if so_not_exist:
                            oder_line_rec.append(
                                (0, 0, {'product_id': line.product_id.id,
                                        'product_uom_qty': line.product_uom_qty,
                                        'name': line.name,
                                        'product_uom': line.product_uom,
                                        'location_id': selected_picking_order.location_id.id,
                                        'location_dest_id': selected_picking_order.location_dest_id.id,
                                        }))

            selected_picking_order.write(picking_order_vals)

            for sale in picking_orders:
                if sale.id != selected_picking_order.id:
                    sale.unlink()
