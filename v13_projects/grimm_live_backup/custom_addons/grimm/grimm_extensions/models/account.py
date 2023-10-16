# -*- coding: utf-8 -*-


from odoo import models, fields, api, _

from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare


MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
}


#
# class AccountConfigSettings(models.TransientModel):
#     _inherit = 'account.config.settings'
#
#     @api.model
#     def _set_proforma_in_settings(self):
#         self.create({'group_proforma_invoices': True}).execute()

class AccountAccount(models.Model):
    _name = "account.account"
    _inherit = ['account.account', 'mail.thread']

    name = fields.Char(required=True, index=True, track_visibility='onchange')
    code = fields.Char(size=64, required=True, index=True, track_visibility='onchange')

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def post(self):
        for rec in self:
            if rec.has_invoices:
                if rec.invoice_ids:
                    for invoice in rec.invoice_ids:
                        sale_order_id = self.env['sale.order'].search(
                            [('name', '=', invoice.invoice_origin)], limit=1)
                        if sale_order_id and sale_order_id.state == 'prepayment':
                            sale_order_id.action_confirm()
        return super(AccountPayment, self).post()

    @api.model
    def default_get(self, fields):
        rec = super(AccountPayment, self).default_get(fields)
        invoice_defaults = self.resolve_2many_commands('invoice_ids', rec.get('invoice_ids'))
        if invoice_defaults and len(invoice_defaults) == 1:
            invoice = invoice_defaults[0]
            rec['communication'] = invoice['name']
            rec['currency_id'] = invoice['currency_id'][0]
            rec['payment_type'] = invoice['type'] in (
                'out_invoice', 'in_refund') and 'inbound' or 'outbound'
            rec['partner_type'] = MAP_INVOICE_TYPE_PARTNER_TYPE[invoice['type']]
            rec['partner_id'] = invoice['partner_id'][0]
            rec['amount'] = invoice['amount_residual']
        return rec


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    @api.model
    def create(self, vals):
        result = super(AccountInvoice, self).create(vals)
        for line in result.invoice_line_ids:
            if len(line.tax_ids) > 1 and self.env.user.id > 2:
                raise ValidationError(_(
                    'You can enter only one tax per line. Please check this product %s. \n Or contact Administrator.' % str(
                        line.product_id.display_name)))
        return result

    def write(self, vals):
        result = super(AccountInvoice, self).write(vals)
        for res in self:
            for line in res.invoice_line_ids:
                if len(line.tax_ids) > 1 and self.env.user.id > 2:
                    raise ValidationError(_(
                        'You can enter only one tax per line. Please check this product %s. \n Or contact Administrator.' % str(
                            line.product_id.display_name)))
        return result

    def _get_bf_from_so(self):
        for record in self:
            sale_order_id = self.env['sale.order'].search([('name', '=', record.invoice_origin)], limit=1)
            if sale_order_id:
                self.beneficiary = sale_order_id.beneficiary or False
            else:
                self.beneficiary = False

    @api.model
    def _get_default_invoice_date(self):
        return fields.Date.today() if self._context.get('default_type', 'entry') in (
            'in_invoice', 'in_refund', 'in_receipt') else False

    invoice_date = fields.Date(string='Invoice/Bill Date', readonly=True, index=True, copy=False,
                               states={'draft': [('readonly', False)],'proforma2': [('readonly', False)]},
                               default=_get_default_invoice_date)

    beneficiary = fields.Many2one('res.partner', 'Beneficiary', states={
        'confirmed': [('readonly', True)]}, compute=_get_bf_from_so)
    sale_order_client_order_refs = fields.Char(compute="_compute_customer_refs", string='Kundenreferenz', copy=False,
                                               store=True)  # , search="_search_customer_refs")
    payment_dates = fields.Char(compute="_compute_payment_dates", string='Zahlungsdatum', copy=False)

    # Variable: prepayment_order_state
    #           -> make sale.order state accessible in account.invoice
    # Method:   _compute_prepayment_state
    #           -> get value of state from referenced sale.order
    #           -> depends on origin - string with sale.order.name
    prepayment_order_state = fields.Char(string="Prepayment State", compute="_compute_prepayment_state")

    # Link to reference origin
    origin_link = fields.Many2one('sale.order', 'Referenzbeleg', compute="_compute_origin_link")
    state = fields.Selection(selection_add=[('proforma', 'Proforma'), ('proforma2', 'Proforma')])
    # state = fields.Selection(selection=[
    #     ('draft', 'Draft'), ('proforma', 'Proforma'), ('proforma2', 'Proforma'), ('open', 'Open'),
    #     ('posted', 'Posted'),
    #     ('cancel', 'Cancelled')
    # ], string='Status', required=True, readonly=True, copy=False, tracking=True,
    #     default='draft')

    # Get sale order for origin for relation link
    # -> link is generated for first origin in invoice.origin (comma separated)
    @api.depends('invoice_origin')
    def _compute_origin_link(self):
        for invoice in self:
            invoice.origin_link = False
            sale_pool = self.env['sale.order']
            if invoice.invoice_origin:
                for origin in invoice.invoice_origin.split(','):
                    invoice.origin_link = sale_pool.search([('name', '=', origin)], limit=1)
                    break

    @api.depends('invoice_origin')
    def _compute_prepayment_state(self):
        for invoice in self:
            sale_pool = self.env['sale.order']
            invoice.prepayment_order_state = 'draft'
            if invoice.invoice_origin:
                for origin in invoice.invoice_origin.split(','):
                    sales = sale_pool.search([('name', '=', origin)])
                    for sale in sales:
                        if sale.state:
                            invoice.prepayment_order_state = sale.state
                            break

    delivery_dates = fields.Char(compute="_compute_delivery_dates", string="Lieferdatum", copy=False)

    @api.depends('invoice_origin')
    def _compute_delivery_dates(self):
        for invoice in self:
            sale_pool = self.env['sale.order']
            t_delivery_dates = ""
            count = 0
            last_week = 0
            if invoice.invoice_origin:
                for origin in invoice.invoice_origin.split(','):
                    sales = sale_pool.search([('name', '=', origin)])
                    for sale in sales:
                        if sale.picking_ids:
                            for pick in sale.picking_ids:
                                if pick.state not in ['draft', 'cancel']:
                                    if count > 1 and sale.picking_ids:
                                        t_delivery_dates += ","
                                    if pick and pick.scheduled_date:
                                        week = int(fields.Date.from_string(pick.scheduled_date).strftime("%W"))

                                        if week != last_week:
                                            t_delivery_dates = ' '.join((t_delivery_dates,
                                                                         fields.Date.from_string(
                                                                             pick.scheduled_date).strftime(
                                                                             "KW %W/%Y")))
                                            count += 1
                                            last_week = week
            invoice.delivery_dates = t_delivery_dates

    @api.depends('invoice_line_ids')
    def _compute_payment_dates(self):
        for invoice in self:
            t_payment_dates = []
            for m_line in invoice.invoice_line_ids:
                if m_line.payment_id and m_line.payment_id.state not in ['cancelled'] and m_line.payment_id.payment_date:
                    t_payment_dates.append(m_line.payment_id.payment_date.strftime("%d.%m.%y"))
            invoice.payment_dates = ', '.join(list(set(t_payment_dates)))

    @api.depends('invoice_origin')
    def _compute_customer_refs(self):
        for invoice in self:
            sale_pool = self.env['sale.order']
            client_ref = ""
            count = 0
            if invoice.invoice_origin:
                for origin in invoice.invoice_origin.split(','):
                    sales = sale_pool.search([('name', '=', origin)])
                    for sale in sales:
                        if count > 0 and sale.client_order_ref:
                            client_ref += ","
                        if sale.client_order_ref:
                            client_ref = ' '.join((client_ref, sale.client_order_ref)).encode('utf-8')
                        count += 1
            invoice.sale_order_client_order_refs = client_ref

    def confirm_payment(self):
        for invoice in self:
            sale_order_id = self.env['sale.order'].search(
                [('name', '=', invoice.invoice_origin)], limit=1)
            if sale_order_id.state == 'prepayment':
                sale_order_id.action_confirm()

    @api.onchange('purchase_id')
    def purchase_order_change(self):
        if not self.purchase_id:
            return {}
        if self.purchase_id.sale_order_id:
            self.user_id = self.purchase_id.sale_order_id.user_id
        res = super(AccountInvoice, self).purchase_order_change()
        return res

    def action_invoice_open(self):
        # # Does not allow if the vendor bill belongs to a sales order with customer Partenics
        # if self.purchase_id_copy and self.purchase_id_copy.sale_order_id.partner_id.id == 87942 and self.env.user.company_id.id == 1:
        #     raise UserError(_("Please switch the company to Partenics in order to proceed"))
        # lots of duplicate calls to action_invoice_open, so we remove those already open
        to_open_invoices = self.filtered(lambda inv: inv.state != 'open')
        if to_open_invoices.filtered(lambda inv: inv.state != 'draft' and inv.state != 'proforma2'):
            raise UserError(_("Invoice must be in draft state in order to validate it."))
        if to_open_invoices.filtered(
                lambda inv: float_compare(inv.amount_total, 0.0, precision_rounding=inv.currency_id.rounding) == -1):
            raise UserError(_(
                "You cannot validate an invoice with a negative total amount. You should create a credit note instead."))
        to_open_invoices.action_date_assign()
        to_open_invoices.action_move_create()
        return to_open_invoices.invoice_validate()


##############################################################################
#
# AccountInvoiceLine
#  - inherit
#
# @char line_no Positionsnummerierung
#
# _get_line_numbers
#  - Generierung der Positionsnummerierung nach folgendem Schema
#     -> wenn keine Kategorie, dann fortlaufende Nummerierung
#     -> wenn Kategorie mit sub_counter dann wird eine separate Nummerierung
#        mit Basis der vorhergenden Positionsnummer gestartet
#
##############################################################################

class AccountInvoiceLine(models.Model):
    _inherit = 'account.move.line'
    _order = 'move_id, sequence, layout_category_sequence, id'

    line_no = fields.Char(compute="_get_line_numbers", string="Line Number", readonly=False, default=False)
    layout_category_id = fields.Many2one('sale.layout_category', string='Section')
    layout_category_sequence = fields.Integer(related='layout_category_id.sequence', store=True)

    def _get_line_numbers(self):
        line_num = 0
        sub_num = 1
        cat_id = False
        self.line_no = ""
        for line_rec in self:
            if line_rec.layout_category_id and cat_id and line_rec.layout_category_id.sub_counter:
                line_rec.line_no = str(line_num) + '.' + str(sub_num)
                sub_num += 1
            elif line_rec.layout_category_id and line_rec.layout_category_id.sub_counter:
                cat_id = True
                sub_num = 1
                line_rec.line_no = str(line_num) + '.' + str(sub_num)
                sub_num += 1
            else:
                line_num += 1
                line_rec.line_no = line_num
                cat_id = False

    @api.onchange('product_id')
    def _onchange_product_id(self):
        super(AccountInvoiceLine, self)._onchange_product_id()
        for line in self:
            currency = line.move_id.currency_id
            if not line.product_id or line.display_type in ('line_section', 'line_note'):
                continue

            line.name = line._get_computed_name()
            line.account_id = line._get_computed_account()
            line.tax_ids = line._get_computed_taxes()
            line.product_uom_id = line._get_computed_uom()
            line.price_unit = line._get_computed_price_unit()

            # Manage the fiscal position after that and adapt the price_unit.
            # E.g. mapping a price-included-tax to a price-excluded-tax must
            # remove the tax amount from the price_unit.
            # However, mapping a price-included tax to another price-included tax must preserve the balance but
            # adapt the price_unit to the new tax.
            # E.g. mapping a 10% price-included tax to a 20% price-included tax for a price_unit of 110 should preserve
            # 100 as balance but set 120 as price_unit.
            if line.tax_ids and line.move_id.fiscal_position_id:
                line.price_unit = line._get_price_total_and_subtotal()['price_subtotal']
                line.tax_ids = line.move_id.fiscal_position_id.map_tax(line.tax_ids._origin, partner=line.move_id.partner_id)
                accounting_vals = line._get_fields_onchange_subtotal(price_subtotal=line.price_unit, currency=line.move_id.company_currency_id)
                balance = accounting_vals['debit'] - accounting_vals['credit']
                line.price_unit = line._get_fields_onchange_balance(balance=balance).get('price_unit', line.price_unit)

            # Convert the unit price to the invoice's currency.
            company = line.move_id.company_id
            line.price_unit = company.currency_id._convert(line.price_unit, line.move_id.currency_id, company, line.move_id.date)
            if company.currency_id != currency:
                line.price_unit = line.price_unit * \
                                  currency.with_context(
                                      dict(self._context or {}, date=self.move_id.invoice_date)).rate

        if len(self) == 1:
            return {'domain': {'product_uom_id': [('category_id', '=', self.product_uom_id.category_id.id)]}}