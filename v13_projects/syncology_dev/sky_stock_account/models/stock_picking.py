from odoo import fields, models, api, _
from datetime import date


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    receipt_id = fields.Many2one('account.move', 'Receipt')
    payment_status = fields.Boolean('Payment Status', store=True, copy=False)
    total = fields.Float(string='Total', compute='_compute_subtotal_custom')

    @api.depends('move_ids_without_package', 'move_ids_without_package.subtotal')
    def _compute_subtotal_custom(self):
        for picking in self:
            amount = 0.0
            for move in picking.move_ids_without_package:
                amount = amount + move.subtotal
            picking.total = amount

    def action_done(self):
        """
        Overridden action_done() method to call custom_method_create_journal_entries() method
        -------------------------------------------------------------------------------------
        @param self: object pointer
        """
        res = super(StockPicking, self).action_done()
        self.custom_method_create_journal_entries()
        return res

    def custom_method_create_journal_entries(self):
        """
        This method will be used for creating Journal Entries according to the contact type and operation type
        ------------------------------------------------------------------------------------------------------
        @param self: object pointer
        """
        receipts_obj = self.env['account.move']
        product_obj = self.env['product.product']

        if self.contact_type == 'student' and self.picking_type_id.code == 'outgoing':
            account_vals = {}
            line_vals = []
            account_vals.update({'partner_id': self.student_id.partner_id.id,
                                 'invoice_date': date.today(),
                                 'type': 'out_receipt',
                                 'ref': self.name})
            for line in self.move_ids_without_package:
                product = product_obj.search([('id', '=', line.product_id.id)])
                line_vals.append((0, 0, {'product_id': line.product_id.id,
                                         'quantity': line.product_uom_qty or line.quantity_done,
                                         'product_uom_id': line.product_uom.id,
                                         'price_unit': product.lst_price,
                                         'tax_ids': product.taxes_id}))
            account_vals.update({'invoice_line_ids': line_vals})
            receipt = receipts_obj.create(account_vals)
            self.receipt_id = receipt

        if self.contact_type == 'external' and self.picking_type_id.code == 'incoming':
            accounts_vals = {}
            line_vals = []
            accounts_vals.update({'partner_id': self.partner_id.id,
                                  'invoice_date': date.today(),
                                  'date': date.today(),
                                  'type': 'in_receipt',
                                  'ref': self.name})
            for line in self.move_ids_without_package:
                product = product_obj.search([('id', '=', line.product_id.id)])
                line_vals.append((0, 0, {'product_id': line.product_id.id,
                                         'quantity': line.product_uom_qty,
                                         'product_uom_id': line.product_uom.id,
                                         'price_unit': product.standard_price,
                                         'tax_ids': product.supplier_taxes_id}))
            accounts_vals.update({'invoice_line_ids': line_vals})
            receipt = receipts_obj.create(accounts_vals)
            self.receipt_id = receipt

        if self.contact_type == 'student' and self.picking_type_id.code == 'incoming':
            accounts_vals = {}
            line_vals = []
            accounts_vals.update({'partner_id': self.student_id.partner_id.id,
                                  'invoice_date': date.today(),
                                  'type': 'out_refund',
                                  'ref': self.name})
            for line in self.move_ids_without_package:
                product = product_obj.search([('id', '=', line.product_id.id)])
                line_vals.append((0, 0, {'product_id': line.product_id.id,
                                         'quantity': line.product_uom_qty,
                                         'product_uom_id': line.product_uom.id,
                                         'price_unit': product.lst_price,
                                         'tax_ids': product.taxes_id}))
            accounts_vals.update({'invoice_line_ids': line_vals})
            receipt = receipts_obj.create(accounts_vals)
            self.receipt_id = receipt

        if self.contact_type == 'external' and self.picking_type_id.code == 'outgoing':
            accounts_vals = {}
            line_vals = []
            accounts_vals.update({'partner_id': self.partner_id.id,
                                  'invoice_date': date.today(),
                                  'date': date.today(),
                                  'type': 'in_refund',
                                  'ref': self.name})

            for line in self.move_ids_without_package:
                product = product_obj.search([('id', '=', line.product_id.id)])
                line_vals.append((0, 0, {'product_id': line.product_id.id,
                                         'quantity': line.product_uom_qty,
                                         'product_uom_id': line.product_uom.id,
                                         'price_unit': product.standard_price,
                                         'tax_ids': product.supplier_taxes_id}))

            accounts_vals.update({'invoice_line_ids': line_vals})
            receipt = receipts_obj.create(accounts_vals)
            self.receipt_id = receipt
