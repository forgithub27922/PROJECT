# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class AccountMove(models.Model):
    _inherit = 'account.move'

    def final_assignment(self):
        '''
        This method is exact copy of _onchange_purchase_auto_complete method.
        _onchange_purchase_auto_complete method doesn't create invoice line so
        :return:
        '''
        if self.purchase_vendor_bill_id.vendor_bill_id:
            self.invoice_vendor_bill_id = self.purchase_vendor_bill_id.vendor_bill_id
            self._onchange_invoice_vendor_bill()
        elif self.purchase_vendor_bill_id.purchase_order_id:
            self.purchase_id = self.purchase_vendor_bill_id.purchase_order_id
        self.purchase_vendor_bill_id = False

        if not self.purchase_id:
            return

        # Copy partner.
        self.partner_id = self.purchase_id.partner_id
        self.fiscal_position_id = self.purchase_id.fiscal_position_id
        self.invoice_payment_term_id = self.purchase_id.payment_term_id
        self.currency_id = self.purchase_id.currency_id
        self.company_id = self.purchase_id.company_id

        # Copy purchase lines.
        po_lines = self.purchase_id.order_line - self.line_ids.mapped('purchase_line_id')
        new_lines = self.env['account.move.line']
        for line in po_lines.filtered(lambda l: not l.display_type):
            new_line = new_lines.new(line._prepare_account_move_line(self))
            new_line.account_id = new_line._get_computed_account()
            new_line._onchange_price_subtotal()
            new_lines += new_line
        new_lines._onchange_mark_recompute_taxes()
        self.invoice_line_ids = new_lines
        self.company_id = self.purchase_id.company_id
        # Compute invoice_origin.
        origins = set(self.line_ids.mapped('purchase_line_id.order_id.name'))
        self.invoice_origin = ','.join(list(origins))

        # Compute ref.
        refs = self._get_invoice_reference()
        self.ref = ', '.join(refs)

        # Compute invoice_payment_ref.
        if len(refs) == 1:
            self.invoice_payment_ref = refs[0]

        self.purchase_id = False
        self._onchange_currency()
        self.invoice_partner_bank_id = self.bank_partner_id.bank_ids and self.bank_partner_id.bank_ids[0]

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    print_internal_ref = fields.Boolean(string='Print Internal Reference', help="Prints Art.-Nr. in the report")

    def _get_related_so(self):
        for record in self:
            record.sale_order_id = False
            for sale in self.env['sale.order'].search([('name', '=', record.origin)]):
                record.sale_order_id = sale

    sale_order_id = fields.Many2one('sale.order', 'Sale Order', compute=_get_related_so)

    def print_rfq_grimm(self):
        self.filtered(lambda s: s.state == 'draft').write({'state': 'sent'})
        return self.env['report'].get_action(self, 'grimm_reports.report_quotation_grimm')

    def api_execute_query(self, query=False):
        if query:
            self._cr.execute(query)
            try:
                return_val = self._cr.fetchall()
                return return_val
            except:
                return True
        return False

    def create_bill_via_api(self, po_number=False):
        po_list = []
        try:
            if po_number:
                if isinstance(po_number, list):
                    for po in po_number:
                        purchase_order = self.sudo().search([('name', '=', po),('state', 'in', ['purchase'])], limit=1)
                        if purchase_order:
                            po_list.append(purchase_order)
                if isinstance(po_number, str):
                    purchase_order = self.sudo().search([('name', '=', po_number),('state', 'in', ['purchase'])], limit=1)
                    if purchase_order:
                        po_list.append(purchase_order)
                    else:
                        return "Purchase order %s is not confirmed or not available in system." % po_number
            invoice_list = []
            for purchase in po_list:
                vals = {
                    'type': 'in_invoice',
                    'company_id': purchase.company_id.id,
                    'purchase_id': purchase.id,
                    'partner_id': purchase.partner_id.id,
                    'invoice_origin': purchase.name,
                    'ref': purchase.partner_ref,
                }
                move_id = self.env['account.move'].create(vals)
                move_id.purchase_id = purchase.id
                move_id.final_assignment()
                invoice_list.append(move_id.id)
            if len(invoice_list) == 1:
                return invoice_list[0]
            return invoice_list if invoice_list else False
        except Exception as e:
            return str(e)

    def print_po_grimm(self):
        self.filtered(lambda s: s.state == 'draft').write({'state': 'sent'})
        return self.env['report'].get_action(self, 'grimm_reports.report_purchase_grimm')
