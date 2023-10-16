##########################################################################################
#
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#    Copyright (C) 2020 Skyscend Business Solutions Pvt. Ltd. (http://www.skyscendbs.com)
#
##########################################################################################
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date, timedelta


class AccountMove(models.Model):
    _name = 'account.move'
    _inherit = ['account.move', 'barcodes.barcode_events_mixin']

    def on_barcode_scanned(self,barcode):
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
            for invoice in self:
                if invoice.move_type != 'entry':
                    if invoice.state == 'posted':
                        raise ValidationError(_('The entry %s is already posted.') % (invoice.name))
                    iv_line = invoice.invoice_line_ids.filtered(lambda r: r.product_id.id == product.id)
                    if len(iv_line) > 0:
                        iv_line = iv_line[0]
                        iv_line.sudo().with_context(check_move_validity=False).write({'quantity': iv_line.quantity + 1})
                        iv_line._onchange_product_id()
                        iv_line._onchange_price_subtotal()
                        invoice._onchange_invoice_line_ids()
                    else:
                        iv_line_vals = {
                            'product_id': product.id or False,
                            'account_id': False,
                            'name': product.display_name,
                            'quantity': 1.0,
                            'currency_id': invoice.currency_id.id,
                            'price_unit': product.list_price,
                        }
                        invoice.sudo().with_context(check_move_validity=False).invoice_line_ids = [(0, 0, iv_line_vals)]
                        line = invoice.invoice_line_ids and invoice.invoice_line_ids[-1]
                        line._onchange_product_id()
                        line._onchange_price_subtotal()
                        invoice._onchange_invoice_line_ids()
        else:
            raise ValidationError(_("Invalid Barcode !!!..."))


