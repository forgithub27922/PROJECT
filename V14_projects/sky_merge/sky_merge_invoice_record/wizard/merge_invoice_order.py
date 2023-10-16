from odoo import models, fields, _, api
from odoo.exceptions import UserError


class MergeInvoice(models.TransientModel):
    _name = 'merge.invoice.order.wiz'
    _description = 'Merge the invoice order'

    merge_type = fields.Selection(selection=[('new_invoice_state_cancel',
                                              'New Invoice/Bill and Cancel Selected.'),
                                             ('new_invoice_delete_order',
                                              'New Invoice/Bill and Delete all selected Invoices.'),
                                             ('select_exist_invoice_state_cancel',
                                              'Merge Invoices/Bills on existing selected Invoice/Bill and cancel others.'),
                                             ('select_exist_invoice_delete_order',
                                              'Merge Invoices/Bills on existing selected Invoice/Bill and delete others.')],
                                  string='Merge Type', default='new_invoice_state_cancel')

    merge_invoice_id = fields.Many2one('account.move', 'Invoice')

    @api.onchange('merge_type')
    def on_change_invoices(self):
        """
        This method will help to show selected order in merge_invoice_id Field
        @:param : self:object Pointer
        """
        invoice_lst = []
        invoice_records = {}
        invoice_data = self.env['account.move'].browse(self._context.get('active_ids', []))
        if self.merge_type in ['select_exist_invoice_state_cancel', 'select_exist_invoice_delete_order']:
            for invoice in invoice_data:
                invoice_lst.append(invoice.id)
            invoice_records['domain'] = {
                'merge_invoice_id': [('id', 'in', invoice_lst)]
            }
            return invoice_records

    def merge_invoice_orders(self, lenes=None):
        """
        This Method will help to merge invoice orders
        @:param: self:object pointer
        """
        invoice_data = self.env['account.move'].browse(self._context.get('active_ids', []))
        print("\n\n INVOICES", invoice_data)
        # data = self._context.get('active_ids', [])
        # print("\n\n\n ::::::> DATA", data)
        # data22 = self._context
        # print("\n\n\n ::::::::> DATA22", data22)
        # check the invoices length...
        if (len(self._context.get('active_ids', []))) < 2:
            raise UserError(_('Please select at least two invoices to perform merge operation'))

        # check the states of invoices...
        if any(invoice.state != 'draft' for invoice in invoice_data):
            raise UserError(_('Please select those invoices which are in Draft state.'))

        # check the customer of invoice...
        first_invoice_record = invoice_data[0].invoice_partner_display_name
        print('\n\n :::::::> I', first_invoice_record)
        for invoice_record in invoice_data:
            print("\n\n\n:::::::::> CUSTOMER", first_invoice_record)
            if invoice_record.invoice_partner_display_name != first_invoice_record:
                raise UserError(_('Please select same Customer invoices to perform merge operation.'))

        # Merge Invoices :-

        # Option-1 : New Invoice/Bill and Cancel Selected.
        if self.merge_type == 'new_invoice_state_cancel':
            invoice_obj = self.env['account.move']
            fst_record = invoice_data[0]
            print("\n\n\n :::::::> FST RECORD", fst_record)
            fst_record_name = fst_record.name
            print("\n\n\n :::::::> FST RECORD NAME", fst_record_name)
            invoice_rec = []
            invoice_order_id_if_exist = True
            invoice_vals = {
                'move_type': fst_record.move_type,
                'partner_id': fst_record.partner_id.id,
                'invoice_date': fst_record.invoice_date,
                'invoice_date_due': fst_record.invoice_date_due,
                'invoice_payment_term_id': fst_record.invoice_payment_term_id,
                'invoice_line_ids': invoice_rec
            }
            for order in invoice_data:
                for line in order.invoice_line_ids:
                    print("\n\n\n ::::::> LINE", line)
                    for order_dict in invoice_rec:
                        print("\n\n\n :::::::> ORDER DICT", order_dict)
                        if order_dict[2].get('product_id') == line.product_id.id:
                            qty = order_dict[2].get('quantity')
                            order_dict[2].update({
                                'quantity': qty + line.quantity
                            })
                            invoice_order_id_if_exist = False
                    if invoice_order_id_if_exist:
                        invoice_rec.append((0, 0, {
                            'product_id': line.product_id.id,
                            'quantity': line.quantity,
                            'price_unit': line.price_unit,
                            'tax_ids': line.tax_ids
                        }))
            print("\n\n\n::::::::: REC ", invoice_rec)
            data = invoice_obj.create(invoice_vals)
            print("\n\ndata", data)
            for selected_invoice in invoice_data:
                selected_invoice.state = 'cancel'

        # option-2: New Invoice/Bill and Delete all selected Invoices.
        elif self.merge_type == 'new_invoice_delete_order':
            invoice_obj = self.env['account.move']
            fst_record = invoice_data[0]
            invoice_rec = []
            invoice_order_id_if_exist = True
            invoice_vals = {
                'move_type': fst_record.move_type,
                'partner_id': fst_record.partner_id.id,
                'invoice_date': fst_record.invoice_date,
                'invoice_date_due': fst_record.invoice_date_due,
                'invoice_payment_term_id': fst_record.invoice_payment_term_id,
                'invoice_line_ids': invoice_rec
            }
            for order in invoice_data:
                for line in order.invoice_line_ids:
                    print("\n\n\n ::::::> LINE", line)
                    for order_dict in invoice_rec:
                        print("\n\n\n :::::::> ORDER DICT", order_dict)
                        if order_dict[2].get('product_id') == line.product_id.id:
                            qty = order_dict[2].get('quantity')
                            order_dict[2].update({
                                'quantity': qty + line.quantity
                            })
                            invoice_order_id_if_exist = False
                    if invoice_order_id_if_exist:
                        invoice_rec.append((0, 0, {
                            'product_id': line.product_id.id,
                            'quantity': line.quantity,
                            'price_unit': line.price_unit,
                            'tax_ids': line.tax_ids
                        }))
            print("\n\n\n::::::::: REC ", invoice_rec)
            data = invoice_obj.create(invoice_vals)
            print("\n\n data", data)
            for selected_invoice in invoice_data:
                print("selected_invoice", selected_invoice)
                selected_invoice[0].unlink()

        # option-3 : Merge Invoices/Bills on existing selected Invoice/Bill and cancel others
        elif self.merge_type == 'select_exist_invoice_state_cancel':
            invoice_obj = self.env['account.move']
            selected_invoice = self.merge_invoice_id
            invoice_lines = selected_invoice.invoice_line_ids
            print("\n\n\n ::::::::>", invoice_lines)
            invoice_rec = []
            invoice_lines_if_exist = True
            for order in invoice_data:

                if order.id != selected_invoice.id:
                    for line in order.invoice_line_ids:
                        for in_line in selected_invoice.invoice_line_ids:
                            if in_line.product_id.id == line.product_id.id:
                                qty = in_line.quantity
                                in_line.quantity = qty + line.quantity
                                invoice_lines_if_exist = False
                            for lenes in order.line_ids:
                                print("\n\n\n ::::::::{{{ LINE IDS ", lenes)
                        if invoice_lines_if_exist:
                            invoice_rec.append((0, 0, {
                                'product_id': line.product_id.id,
                                'quantity': line.quantity,
                                'price_unit': line.price_unit,
                                'tax_ids': line.tax_ids
                            }))

            selected_invoice.write({
                'invoice_line_ids': invoice_rec
            })
            for invoice in invoice_data:
                if invoice.id != selected_invoice.id:
                    invoice.state = 'cancel'

        # option-4 : Merge Invoices/Bills on existing selected Invoice/Bill and delete others
        else:
            selected_invoice = self.merge_invoice_id
            invoice_lines = selected_invoice.invoice_line_ids
            print("\n\n\n ::::::::>", invoice_lines)
            invoice_rec = []
            invoice_lines_if_exist = True
            for order in invoice_data:

                if order.id != selected_invoice.id:
                    for line in order.invoice_line_ids:
                        for in_line in selected_invoice.invoice_line_ids:
                            if in_line.product_id.id == line.product_id.id:
                                qty = in_line.quantity
                                in_line.quantity = qty + line.quantity
                                invoice_lines_if_exist = False
                            for lenes in order.line_ids:
                                print("\n\n\n ::::::::{{{ LINE IDS ", lenes)
                        if invoice_lines_if_exist:
                            invoice_rec.append((0, 0, {
                                'product_id': line.product_id.id,
                                'quantity': line.quantity,
                                'price_unit': line.price_unit,
                                'tax_ids': line.tax_ids
                            }))
            selected_invoice.write({
                'invoice_line_ids': invoice_rec
            })
            for invoice in invoice_data:
                if invoice.id != selected_invoice.id:
                    invoice[0].unlink()
