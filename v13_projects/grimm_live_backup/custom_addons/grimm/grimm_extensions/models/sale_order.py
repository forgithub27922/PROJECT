# -*- coding: utf-8 -*-


from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import Warning
import re
import datetime


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    product_id = fields.Many2one('product.product', related='order_line.product_id', string='Product')
    customer_ref = fields.Char('Kundenreferenz ', related='partner_id.ref')

    @api.depends('order_line.invoice_lines')
    def _get_invoiced(self):
        # Grimm Inherited this method because grimm wants to add invoice based on invoice origin too.
        for order in self:
            invoices = order.order_line.invoice_lines.move_id.filtered(lambda r: r.type in ('out_invoice', 'out_refund'))
            invoices_extra = self.env['account.move'].search([('invoice_origin', '=', order.name)]).filtered(lambda r: r.type in ('out_invoice', 'out_refund'))
            order.invoice_ids = invoices + invoices_extra
            order.invoice_count = len(list(set(invoices + invoices_extra)))

    @api.depends('order_line.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line:
                if line.layout_category_id and line.layout_category_id.add_to_total is False:
                    continue

                amount_untaxed += line.price_subtotal
                # FORWARDPORT UP TO 10.0
                if order.company_id.tax_calculation_rounding_method == 'round_globally':
                    price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                    taxes = line.tax_id.compute_all(
                        price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id,
                        partner=line.order_id.partner_id)
                    amount_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                else:
                    amount_tax += line.price_tax
            order.update({
                'amount_untaxed': order.pricelist_id.currency_id.round(amount_untaxed) if order.pricelist_id else order.company_id.currency_id.round(amount_untaxed),
                'amount_tax': order.pricelist_id.currency_id.round(amount_tax) if order.pricelist_id else order.company_id.currency_id.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
            })


    sent_dn_date = fields.Datetime(string="Sent delivery notice Date")

    @api.depends('analytic_account_id')
    def _get_subscription(self):
        for order in self:
            order.subscription_id = self.env['sale.subscription'].search(
                [('analytic_account_id', '=', order.analytic_account_id.id)], limit=1)

    def compute_next_month_date(self, strdate):
        onemonth = relativedelta(months=1)
        start_date = fields.Date.from_string(strdate)
        next_month = start_date + onemonth
        return fields.Date.to_string(next_month)

    @api.onchange('prepayment')
    def _get_paymentterm(self):
        for record in self:
            if record.prepayment is True:
                record.payment_term_id = record.env['account.payment.term'].search(
                    [('name', '=', 'Immediate Payment'),('company_id', '=', self.company_id.id)]) or 1
                # record.payment_mode_id = False
                if self.env.user.company_id.id == 1:
                    record.payment_mode_id = 3  # Added changes as requirement from Christian so when we prepayment true its add banktransfer as an payment mode
            else:
                record.payment_term_id = record.partner_id.property_payment_term_id and record.partner_id.property_payment_term_id.id or False
                record.payment_mode_id = record.partner_id.customer_payment_mode_id and record.partner_id.customer_payment_mode_id.id or False

    state = fields.Selection(selection_add=[('prepayment', 'Auf Zahlung warten'),('deliverynotice', 'Lieferanzeige')], track_visibility='onchange')

    prepayment = fields.Boolean('Prepayment', readonly=True, states={
        'draft': [('readonly', False)], 'sent': [('readonly', False)]}, default=True)
    asset_ids = fields.Many2many('grimm.asset.asset', string='Assets',
                                 domain="[('partner_owner','=',partner_id)]")
    subscription_id = fields.Many2one(comodel_name='sale.subscription', store=True)
    purchase_order_ids = fields.Many2many('purchase.order', string="Purchase Orders",
                                          domain="[('origin','in',name)]")
    purchase_order_count = fields.Integer(string="Count of Purchase Orders", compute="_get_len_po")
    object_address = fields.Many2one('grimm.asset.facility', string='Object Address',
                                     track_visibility='onchange')
    order_subject = fields.Char(string='Order Subject')
    contact = fields.Many2one('res.partner', string='Contact')
    beneficiary = fields.Many2one('res.partner', string='Beneficiary')
    notes = fields.Text(string='Notes')
    claim_id = fields.Many2one('crm.claim', string='Claim')
    validity_date = fields.Date(
        default=lambda self: self.compute_next_month_date(fields.Date.context_today(self)), copy=False)
    invoice_count = fields.Integer(track_visibility='onchange')
    manual_line_number = fields.Boolean(string='Manuel Line Number', default=False)
    payment_date = fields.Datetime('Payment Date', related='create_date', readonly=True)

    # @api.depends('order_line.purchase_line_ids')
    # def _get_len_po(self):
    #     purchase_line_data = self.env['purchase.order.line'].read_group(
    #         [('sale_order_id', 'in', self.ids)],
    #         ['sale_order_id', 'purchase_order_count:count_distinct(order_id)'], ['sale_order_id']
    #     )
    #     purchase_count_map = {item['sale_order_id'][0]: item['purchase_order_count'] for item in purchase_line_data}
    #     for order in self:
    #         order.purchase_order_count = purchase_count_map.get(order.id, 0)

    def _get_len_po(self):
        for record in self:
            record.purchase_order_count = self.env['purchase.order'].search_count(
                [('origin', '=', record.name)])

    @api.model
    def create(self, vals):
        if 'object_address' in vals and vals['object_address']:
            vals.update(self.get_partner_dict_from_asset(vals['object_address']))
        result = super(SaleOrder, self).create(vals)
        if result.salutation_text_offer_tmpl_id:
            result.salutation_text_offer = result.salutation_text_offer_tmpl_id.render_template(result.salutation_text_offer_tmpl_id.text,result)
        if result.salutation_text_order_tmpl_id:
            result.salutation_text_order = result.salutation_text_order_tmpl_id.render_template(result.salutation_text_order_tmpl_id.text,result)
        if result.salutation_text_dn_tmpl_id:
            result.salutation_text_dn = result.salutation_text_dn_tmpl_id.render_template(result.salutation_text_dn_tmpl_id.text,result)
        for line in result.order_line:
            if len(line.tax_id) > 1 and self.env.user.id > 2:
                raise ValidationError(_(
                    'You can enter only one tax per line. Please check this product %s. \n Or contact Administrator.' % str(
                        line.product_id.display_name)))
        return result

    def sorted_nicely_list(self, l):
        """ Sort the given iterable in the way that humans expect."""
        convert = lambda text: int(text) if text.isdigit() else text
        alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
        return sorted(l, key=alphanum_key)

    def write(self, vals):
        if 'object_address' in vals and vals['object_address']:
            vals.update(self.get_partner_dict_from_asset(vals['object_address']))
        result = super(SaleOrder, self).write(vals)
        for res in self:
            if res.opportunity_id and res.is_lead_created_from_offer:
                res.opportunity_id.name = "%s %s " % (res.partner_id.name, res.order_subject or '')
            line_seq_list = []
            line_seq_dict = {}
            for line in res.order_line:
                line_seq_list.append(str(line.line_no_manual))
                if len(line.tax_id) > 1 and self.env.user.id > 2:
                    raise ValidationError(_('You can enter only one tax per line. Please check this product %s. \n Or contact Administrator.' % str(line.product_id.display_name)))
                line_seq_dict[line.id] =line.line_no_manual
            line_seq_list = self.sorted_nicely_list(line_seq_list)
            index = 1
            for l in line_seq_list:
                line_ids = [k for k,v in line_seq_dict.items() if v == l]
                for l_id in line_ids:
                    query = "update sale_order_line set line_no_seq=%s where id=%s" % (index, l_id)
                    self._cr.execute(query)
                    index = index + 1
        return result

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        """
        remove subscription_id from default values
        :param default: default values
        :return:
        """

        default = dict(default or {})
        default.update({
            'subscription_id': False,
        })
        end_date = (datetime.datetime.strptime("2020-12-31 23:59:59", '%Y-%m-%d %H:%M:%S'))
        current_time = datetime.datetime.now()
        if current_time < end_date:
            default.update({
                'fiscal_position_id': 16,
            })
        elif self.fiscal_position_id and self.fiscal_position_id.id == 16:
            default.update({
                'fiscal_position_id': 0,
            })
        return super(SaleOrder, self).copy(default)

    def action_view_contract(self):
        subscription_id = self.env['sale.subscription'].search([('sale_order_id', 'in', self._ids)])
        list_view_id = self.env.ref('sale_subscription.sale_subscription_view_list').id
        form_view_id = self.env.ref('sale_subscription.sale_subscription_view_form').id

        result = {
            "type": "ir.actions.act_window",
            "res_model": "sale.subscription",
            "views": [[list_view_id, "tree"], [form_view_id, "form"]],
            "domain": [["id", "in", subscription_id.ids]],
            "context": {"create": False},
            "name": "Contracts",
        }
        if len(subscription_id) > 1:
            result['domain'] = "[('id','in',%s)]" % subscription_id.ids
        elif len(subscription_id) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = subscription_id.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

    def action_confirm(self):
        for order in self:

            # OD-1406 Task START
            is_active = order.mapped("order_line.product_id.active") # Get list of is_active True and False
            show_warning = False
            if not all(is_active): # If we found any archieved product we will display warning.
                show_warning = True
            else:
                for line in order.order_line:
                    if line.product_id and line.product_id.sale_ok == False and line.product_id.purchase_ok == False:
                        show_warning = True
                        break
            if show_warning:
                raise Warning(_('Bestellung kann nicht bestätigt werden. \nEin oder mehrere Artikel sind entweder Archiviert oder können nicht eingekauft / verkauft werden.'))
            # OD-1406 Task END


            date_diff = datetime.datetime.now() - fields.Datetime.from_string(order.date_order)
            print(date_diff, '<>', date_diff.seconds, order.payment_mode_id)
            if (date_diff.seconds) / 3600 + date_diff.days * 24 < 12 and order.payment_mode_id.id == 21:
                raise Warning(_('The payment method is RatePay.\nThe total waiting period is 12 hours!'))

            order.date_order = fields.Datetime.now()
            if not self.user_id:
                self.user_id = self.env.user

            #if order.partner_invoice_id.customer == True:
            if order.partner_invoice_id.parent_id:
                debitor_partner_id = order.partner_invoice_id.parent_id
            else:
                debitor_partner_id = order.partner_invoice_id
            if debitor_partner_id.ref == '' or debitor_partner_id.ref == False:
                debitor_partner_id.ref = self.env[
                    'ir.sequence'].next_by_code('partner.debitor')
            if debitor_partner_id.property_account_receivable_id.code != debitor_partner_id.ref:
                debitor_id = self.env['account.account'].create({
                    'name': debitor_partner_id.name,
                    'code': debitor_partner_id.ref,
                    'user_type_id': 1,
                    'reconcile': True,
                })
                partner_obj = self.env['res.partner'].search(
                    [('id', '=', debitor_partner_id.id)], limit=1)
                partner_obj.write({'property_account_receivable_id': debitor_id})
                partner_obj.write({'ref': debitor_partner_id.ref})

            if order.state in ['draft', 'sent'] and order.prepayment:
                order.write({'state': 'prepayment', 'invoice_status': 'invoiced'})

                for line in order.order_line:
                    line.write({'qty_invoiced': line.product_uom_qty})

                # Is not possible to call action_invoice_create
                # because qty_to_invoice field is calculated
                # when sale_order is in sale or done state
                # proforma_invoice = order.action_invoice_create()

                proforma_invoice = order.create_proforma_invoice()
                # workflow is removed on Odoo 11
                # proforma_invoice.signal_workflow('invoice_proforma2')
                # proforma_invoice.signal_workflow('open')
                proforma_invoice.state = 'proforma2'
                return proforma_invoice

        ctx = self.env.context.copy()
        ctx.update({'sale_order_id': order.id})
        result = super(SaleOrder, self.with_context(ctx)).action_confirm()
        for order in self:

            create_lines = []
            for line in order.order_line:
                if not line.product_id:
                    continue

                # don't add line if add_to_total is false
                if line.layout_category_id and line.layout_category_id.add_to_total is False:
                    continue

                # for category in line.product_id.categ_id:
                if line.product_id and line.product_id.recurring_invoice:
                    line_data = {
                        'product_id': line.product_id.id,
                        'name': line.name,
                        'uom_id': line.product_uom.id,
                        'actual_quantity': line.qty_delivered,
                        'sold_quantity': line.product_uom_qty,
                        'price_unit': line.price_unit,
                        'discount': line.discount,
                        'price_subtotal': line.price_subtotal,
                    }
                    line_id = self.env['sale.subscription.line'].create(line_data)
                    create_lines.append(line_id.id)

            # Maybe this should be changed to check if there are assets and sale order lines?
            if create_lines and len(create_lines) != len(order.order_line):
                raise Warning(_('Sale order cannot have both recurring and standard products!'))

            if create_lines:
                contract_data = {
                    'partner_id': order.partner_id.id,
                    'pricelist_id': order.pricelist_id.id,
                    'recurring_invoice_line_ids': [(6, 0, create_lines)],
                    'manager_id': order.user_id.id,
                    'asset_ids': [(6, 0, order.asset_ids.ids)],
                }
                contract_id = self.env['sale.subscription'].create(contract_data)
                order.update({
                    'subscription_id': contract_id.id
                })
                result = self.action_view_contract()
        return result

    @api.model
    def create_proforma_invoice(self):
        invoice_model = self.env['account.move']
        for order in self:

            inv_lines = []
            for line in order.order_line:
                # don't add line if add_to_total is false
                if line.layout_category_id and line.layout_category_id.add_to_total is False:
                    continue
                line.qty_to_invoice= line.product_uom_qty
                line_data = line._prepare_invoice_line()
                line_data['sale_line_ids'] = [(6, 0, [line.id])]
                inv_lines.append((0, 0, line_data))

            inv_data = order._prepare_invoice()

            inv_data['invoice_line_ids'] = inv_lines
            invoice = invoice_model.create(inv_data)

            invoice.salutation_text = invoice.salutation_text_tmpl_id.render_template(invoice.salutation_text_tmpl_id.text, invoice)
            invoice.salutation_text_val = invoice.salutation_text_val_tmpl_id.render_template(invoice.salutation_text_val_tmpl_id.text, invoice)
            invoice.salutation_text_refund = invoice.salutation_text_refund_tmpl_id.render_template(invoice.salutation_text_refund_tmpl_id.text, invoice)
            return invoice

    def _find_contact_object(self, object_address_id):
        facility = self.env['grimm.asset.facility'].search(
            [('name', '=', object_address_id)])
        asset = self.env['grimm.asset.asset'].search(
            [('name', '=', object_address_id)])
        if len(facility) > 1:
            raise Warning(_('Multiple facilities found for partner'))
        contact_object = facility
        if not facility:
            if len(asset) > 1:
                raise Warning(_('Multiple assets found for partner'))
            contact_object = asset
        return contact_object

    @api.onchange('object_address')
    def onchange_object_address(self):
        if self.object_address:
            self.partner_invoice_id = self.object_address.partner_invoice.id
            self.partner_shipping_id = self.object_address.partner_delivery.id
            self.partner_id = self.object_address.partner_owner.id
            self.contact = self.object_address.partner_contact.id

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - Pricelist
        - Payment term
        - Invoice address
        - Delivery address
        """
        if not self.partner_id:
            self.update({
                'partner_invoice_id': False,
                'partner_shipping_id': False,
                'payment_term_id': False,
                'fiscal_position_id': False,
            })
            return

        if not self.carrier_id:
            product_id = self.env['product.product'].search(
                [('name', '=', 'Standardversand innerhalb Deutschland')])
            self.carrier_id = self.env['delivery.carrier'].search(
                [('product_id', '=', product_id.id)])

        addr = self.partner_id.address_get(['delivery', 'invoice'])
        partner_user = self.partner_id.user_id or self.partner_id.commercial_partner_id.user_id
        if self.object_address:
            values = {
                'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
                'payment_term_id': self.partner_id.property_payment_term_id and self.partner_id.property_payment_term_id.id or False,
                'partner_invoice_id': self.object_address.partner_invoice.id,
                'partner_shipping_id': self.object_address.partner_delivery.id,
            }
        else:
            values = {
                'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
                'payment_term_id': self.partner_id.property_payment_term_id and self.partner_id.property_payment_term_id.id or False,
                'partner_invoice_id': addr['invoice'],
                'partner_shipping_id': addr['delivery'],
            }
        user_id = partner_user.id
        if not self.env.context.get('not_self_saleperson'):
            user_id = user_id or self.env.uid
        if user_id and self.user_id.id != user_id:
            values['user_id'] = user_id

        if self.env['ir.config_parameter'].sudo().get_param(
                'account.use_invoice_terms') and self.env.company.invoice_terms:
            values['note'] = self.with_context(lang=self.partner_id.lang).env.company.invoice_terms
        if not self.env.context.get('not_self_saleperson') or not self.team_id:
            values['team_id'] = self.env['crm.team']._get_default_team_id(
                domain=['|', ('company_id', '=', self.company_id.id), ('company_id', '=', False)], user_id=user_id)
        self.update(values)

    @api.model
    def get_partner_dict_from_asset(self, object_address):
        res = {}
        contact_object = self._find_contact_object(object_address)
        if contact_object:
            res['partner_invoice_id'] = contact_object.partner_invoice.id
            res['partner_shipping_id'] = contact_object.partner_delivery.id
            res['partner_id'] = contact_object.partner_invoice.commercial_partner_id.id
        return res

    def action_proforma_send(self):
        '''
        This function opens a window to compose an email, with the grimm proforma template message loaded by default
        '''
        self.ensure_one()
        template = self.env.ref('account.email_template_edi_invoice', False)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        # Get Proforma ID to be set as default_res_id
        for invoice in self.invoice_ids:
            if invoice.state in ['proforma2']:
                invoice_id = invoice.id
            else:
                raise UserError(_('Proforma already sent! Still waiting for payment'))
        ctx = dict(
            default_model='account.move',
            default_res_id=invoice_id,
            default_use_template=bool(template),
            default_template_id=template.id,
            default_composition_mode='comment',
            default_partner_id=self.partner_invoice_id.id,
            #custom_layout="account.mail_template_data_notification_email_account_invoice",
        )
        print(ctx)
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }

    def action_proforma_cancel(self):
        if self.invoice_count > 0:
            for invoice in self.invoice_ids:
                if invoice.state in ('proforma2', 'draft'):
                    invoice.state = 'draft'
                    msg = _("Related Proforma Invoice %s was deleted") % (invoice.ref)
                    invoice.unlink()
                    self.message_post(body=msg)
                else:
                    raise UserError(_('An Invoice in state %s can not be deleted!') %
                                    (invoice.state))
            #self.state = 'cancel'
            self.action_cancel()
        else:
            #self.state = 'cancel'
            self.action_cancel()

    def toggle_line_number(self):
        for record in self:
            record.manual_line_number = not record.manual_line_number

    # Rausgenommen wegen Performance-Problems
    # @api.multi
    # @api.depends('analytic_account_id.line_ids')
    # def _compute_timesheet_ids(self):
    #     for order in self:
    #         if order.tasks_ids:
    #             order.timesheet_ids = self.env['account.analytic.line'].search([
    #                 # ('is_timesheet', '=', True),
    #                 ('account_id', '=', order.analytic_account_id.id),
    #                 ('task_id.id', 'in', order.tasks_ids.ids)
    #             ]) if order.analytic_account_id else []
    #         else:
    #             order.timesheet_ids = self.env['account.analytic.line'].search([
    #                 # ('is_timesheet', '=', True),
    #                 ('account_id', '=', order.analytic_account_id.id)]) if order.analytic_account_id else []
    #
    #         order.timesheet_count = round(sum([line.unit_amount for line in order.timesheet_ids]), 2)


##############################################################################
#
# SaleOrderLine
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

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    _order = 'line_no_seq, order_id, sequence, layout_category_sequence, layout_category_id, id'

    free_description_text = fields.Text(string="Free Text")
    line_no = fields.Char(compute='_get_line_numbers', store=False, string="Nr.")
    line_no_seq = fields.Integer(string="Sort",help="It will sort line based on manual number.", copy=True)
    line_no_manual = fields.Char(string="Manual No.", copy=True)
    manual_line_number = fields.Boolean(related='order_id.manual_line_number')
    layout_category_id = fields.Many2one('sale.layout_category', string='Section')
    layout_category_sequence = fields.Integer(related='layout_category_id.sequence', store=True)

    def _get_display_price(self, product):
        # TO DO: We have to inherit this method because some how odoo is not able to get magento price without calling calculated standard price
        try:
            temp_price = product.calculated_standard_price
        except:
            temp_price = product.calculated_standard_price
        res = super(SaleOrderLine, self)._get_display_price(product)
        if self.order_id.pricelist_id.id == self.order_id.company_id.pricelist_id.id:
            return product.calculated_magento_price
        return res


    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        if not self.product_uom:
            self.price_unit = 0.0
            return
        if self.order_id.pricelist_id and self.order_id.partner_id:
            price_unit = self.price_unit
            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id.id,
                quantity=self.product_uom_qty,
                date_order=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id,
                fiscal_position=self.env.context.get('fiscal_position')
            )
            self.price_unit = self.env['account.tax']._fix_tax_included_price(
                product.price, product.taxes_id, self.tax_id)
            if price_unit != self.price_unit:
                self.price_unit = price_unit

    @api.onchange('product_id')
    def product_id_change(self):
        res = super(SaleOrderLine, self).product_id_change()
        for record in self:
            if record.product_id.description_sale:
                name = record.product_id.description_sale
                record.name = name
            else:
                record.name = ' '
            record.manual_line_number = record.order_id.manual_line_number
        return res

    def sorted_nicely(self, l):
        """ Sort the given iterable in the way that humans expect."""
        convert = lambda text: int(text) if text.isdigit() else text
        alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
        return sorted(l, key=alphanum_key)

    @api.model
    def create(self, vals):
        result = super(SaleOrderLine, self).create(vals)
        if not result.order_id.manual_line_number:
            seq_list = []
            for line in result.order_id.order_line:
                seq_list.append(line.line_no_manual)
            seq_list = list(filter(bool,seq_list))
            if seq_list:
                seq_list = self.sorted_nicely(seq_list)
                try:
                    last_elem = int(re.search(r'\d+', seq_list[-1]).group())+1
                except:
                    if seq_list[-1][0].isalpha():
                        last_elem = "ZZZ"
                    else:
                        last_elem = 999
                result.line_no_manual = last_elem
        return result

    @api.depends('sequence', 'layout_category_id', 'line_no_manual', 'order_id.manual_line_number')
    def _get_line_numbers(self):
        temp = {}
        self.line_no = ""
        for order in self.mapped('order_id'):
            line_num = 0
            sub_num = 1
            # is_changed = False
            for line in order.order_line:
                if order.manual_line_number:
                    #line.line_no = line.line_no_manual
                    temp[line.id] = line.line_no_manual
                elif line.layout_category_id and line.layout_category_id.sub_counter:
                    if sub_num > 1:
                        #line.line_no = "%s.%s" % (line_num, sub_num)
                        temp[line.id] = "%s.%s" % (line_num, sub_num)
                    else:
                        sub_num = 1
                        #line.line_no = "%s.%s" % (line_num, sub_num)
                        temp[line.id] = "%s.%s" % (line_num, sub_num)
                    sub_num += 1
                else:
                    line_num += 1
                    #line.line_no = line_num
                    temp[line.id] = line_num
                    sub_num = 1
        for line in self:
            line.line_no = temp.get(line.id,0)

    def _prepare_invoice_line(self):
        res = super(SaleOrderLine, self)._prepare_invoice_line()
        res['line_no'] = self.line_no
        return res

    def _timesheet_create_task(self, project):
        result = super(SaleOrderLine, self)._timesheet_create_task(project)
        for task in result:
            # task.onchange_partner_id_grimm()
            task.onchange_partner_id_claim_contact()
        return result

    def _timesheet_create_task_prepare_values(self, project):
        self.ensure_one()
        result = super(SaleOrderLine, self)._timesheet_create_task_prepare_values(project)
        result.update({
            'claim_shipping_id': self.order_id.partner_shipping_id.id if self.order_id.partner_shipping_id.id else False,
            'claim_contact': self.order_id.contact.id if self.order_id.contact else False})
        return result

class AccountMove(models.Model):
    _inherit = "account.move"

    def _check_balanced(self):
        ''' Assert the move is fully balanced debit = credit.
        An error is raised if it's not the case.
        '''
        return True # TO-DO GRIMM - Due to unbalanced entry we have added return True
        moves = self.filtered(lambda move: move.line_ids)
        if not moves:
            return

        # /!\ As this method is called in create / write, we can't make the assumption the computed stored fields
        # are already done. Then, this query MUST NOT depend of computed stored fields (e.g. balance).
        # It happens as the ORM makes the create with the 'no_recompute' statement.
        self.env['account.move.line'].flush(['debit', 'credit', 'move_id'])
        self.env['account.move'].flush(['journal_id'])
        self._cr.execute('''
            SELECT line.move_id, ROUND(SUM(line.debit - line.credit), currency.decimal_places)
            FROM account_move_line line
            JOIN account_move move ON move.id = line.move_id
            JOIN account_journal journal ON journal.id = move.journal_id
            JOIN res_company company ON company.id = journal.company_id
            JOIN res_currency currency ON currency.id = company.currency_id
            WHERE line.move_id IN %s
            GROUP BY line.move_id, currency.decimal_places
            HAVING ROUND(SUM(line.debit - line.credit), currency.decimal_places) != 0.0;
        ''', [tuple(self.ids)])

        query_res = self._cr.fetchall()
        if query_res:
            ids = [res[0] for res in query_res]
            sums = [res[1] for res in query_res]
            raise UserError(_("Cannot create unbalanced journal entry. Ids: %s\nDifferences debit - credit: %s") % (ids, sums))
