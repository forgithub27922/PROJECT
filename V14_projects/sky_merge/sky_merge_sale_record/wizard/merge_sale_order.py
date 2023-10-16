from odoo import models, fields, _, api
from odoo.exceptions import UserError


class MergeOrders(models.Model):
    _name = 'merge.sale.order.wiz'
    _description = 'Merge the sale orders'

    merge_type = fields.Selection(
        selection=[('create_order_state_cancel',
                    'Create order by merging orders and cancel the selected orders'),
                   ('create_order_delete_order',
                    'Create new order by merging orders and deleting the selected orders.'),
                   ('select_exist_order_state_cancel',
                    'Select existing order and add other orders to the existing order and cancel others.'),
                   ('select_exist_order_delete_order',
                    'Select existing order and add other orders to the existing order and delete others.')],
        string='Merge Type', default='create_order_state_cancel')

    order_line = fields.One2many('sale.order.line', 'order_id', string='Order Lines')

    merge_sale_order_id = fields.Many2one('sale.order', 'Sale Order')

    @api.onchange('merge_type')
    def on_change_sale_orders(self):
        """
        This method will help to show the many2one field and show the selected sale orders
        :return: res
        @:param self:object pointer
        """
        lst = []
        sale_order = {}
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        if self.merge_type in ['select_exist_order_state_cancel', 'select_exist_order_delete_order']:
            for order in sale_orders:
                lst.append(order.id)
            sale_order['domain'] = {
                'merge_sale_order_id': [('id', 'in', lst)]
            }
            return sale_order

    def merge_sale_orders(self, r=None):
        """
        This Method will help the merge sale orders
        @:param self:object pointer
        """
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        # check the selected orders,selected orders must be greater than 1
        if len(self._context.get('active_ids', [])) < 2:
            raise UserError(_('Please select at_least two sale orders to perform the Merge Operation.'))
        # selected order must be in draft states
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        if any(order.state != 'draft' for order in sale_orders):
            raise UserError('Please select Sale orders which are in Quotation state to perform the Merge Operation.')
        # check the sale order by their customer name
        fst_sale_order = sale_orders[0].partner_id
        for elements in sale_orders:
            if elements.partner_id != fst_sale_order:
                raise UserError(_('Please select same name sale orders to perform the Merge Operation.'))

        # Merge The Sale Orders
        if self.merge_type == 'create_order_state_cancel':
            sale_order_obj = self.env['sale.order']
            oder_line_rec = []
            so_not_exist = True
            for product in sale_orders:

                for line in product.order_line:

                    for order_dict in oder_line_rec:

                        if order_dict[2].get('product_id') == line.product_id.id:
                            qty = order_dict[2].get('product_uom_qty')
                            order_dict[2].update({'product_uom_qty': qty + line.product_uom_qty})
                            so_not_exist = False

                    if so_not_exist:
                        oder_line_rec.append(
                            (0, 0, {'product_id': line.product_id.id,
                                    'product_uom_qty': line.product_uom_qty,
                                    'price_unit': line.price_unit}))

            sale_order_obj.create({
                'partner_id': fst_sale_order.id,
                'order_line': oder_line_rec
            })
            # create the new order and selected orders goes to cancel state
            for order in sale_orders:
                order.state = 'cancel'

        # option:2 - 'Create order by merging orders and delete the selected orders'

        elif self.merge_type == 'create_order_delete_order':
            sale_order_obj = self.env['sale.order']
            oder_line_rec = []
            so_not_exist = True
            for product in sale_orders:

                for line in product.order_line:
                    for order_dict in oder_line_rec:
                        if order_dict[2].get('product_id') == line.product_id.id:
                            qty = order_dict[2].get('product_uom_qty', False)
                            order_dict[2].update({'product_uom_qty': qty + line.product_uom_qty})
                            so_not_exist = False

                    if so_not_exist:
                        oder_line_rec.append(
                            (0, 0, {'product_id': line.product_id.id,
                                    'product_uom_qty': line.product_uom_qty,
                                    'price_unit': line.price_unit}))

            sale_order_obj.create({
                'partner_id': fst_sale_order.id,
                'order_line': oder_line_rec
            })
            for order in sale_orders:
                order.unlink()

        # option:3 - 'Select existing order and add other orders to the existing order and cancel others.'

        elif self.merge_type == 'select_exist_order_state_cancel':

            fst_order = self.merge_sale_order_id
            order_lines = fst_order.order_line

            order = order_lines.product_id

            so_not_exist = True
            oder_line_rec = []
            for product in sale_orders:

                if product.id != fst_order.id:
                    for line in product.order_line:
                        for fst_line in fst_order.order_line:
                            if fst_line.product_id.id == line.product_id.id:
                                qty = fst_line.product_uom_qty
                                fst_line.product_uom_qty = qty + line.product_uom_qty
                                so_not_exist = False

                        if so_not_exist:
                            oder_line_rec.append(
                                (0, 0, {'product_id': line.product_id.id,
                                        'product_uom_qty': line.product_uom_qty,
                                        'price_unit': line.price_unit}))

            fst_order.write({'order_line': oder_line_rec})
            for sale in sale_orders:
                if sale.id != fst_order.id:
                    sale.state = 'cancel'

        # option:4 -'Select existing order and add other orders to the existing order and delete others.'
        else:
            fst_order = self.merge_sale_order_id
            so_not_exist = True
            oder_line_rec = []
            for product in sale_orders:
                if product.id != fst_order.id:
                    for line in product.order_line:
                        for fst_line in fst_order.order_line:
                            if fst_line.product_id.id == line.product_id.id:
                                qty = fst_line.product_uom_qty

                                fst_line.product_uom_qty = qty + line.product_uom_qty

                                so_not_exist = False
                        if so_not_exist:
                            oder_line_rec.append(
                                (0, 0, {'product_id': line.product_id.id,
                                        'product_uom_qty': line.product_uom_qty,
                                        'price_unit': line.price_unit}))

            fst_order.write({'order_line': oder_line_rec})
            for sale in sale_orders:
                if sale.id != fst_order.id:
                    sale.unlink()
