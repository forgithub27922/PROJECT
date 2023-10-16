# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging
from datetime import timedelta
from functools import partial

import psycopg2
import pytz
import re
from pytz import timezone
from datetime import datetime

from odoo import api, fields, SUPERUSER_ID, models, tools, _
from odoo.tools import float_is_zero, float_round
from odoo.exceptions import ValidationError, UserError
from odoo.http import request
from odoo.osv.expression import AND
import base64

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = "pos.order"

    def action_receipt_to_customer_auto(self):
        attachModel = self.env['ir.attachment']
        name = self.noorderns.replace('_', ' ')
        client = {
            'email': self.partner_id.email or '',
            'name': self.partner_id.name or '',
        }        
        message = _("<p>Dear %s,<br/>Here is your electronic ticket for the %s. </p>") % (client['name'], name)
        filename = 'Receipt-' + name + '.jpg'
        cfdi_filename = ('%s-%s-MX-Invoice-3.3.xml' % (self.account_move.journal_id.code, self.account_move.payment_reference)).replace('/', '')
        attach_id = attachModel.search([('name', '=', cfdi_filename), ('res_id', '=', self.account_move.id), ('res_model', '=', self.account_move._name)])
        receipt = ''
        mail_values = {
            'subject': _('Receipt %s', name),
            'body_html': message,
            'author_id': self.env.user.partner_id.id,
            'email_from': self.env.company.email or self.env.user.email_formatted,
            'email_to': client['email'],
            'attachment_ids': [(4, attach_id.id)],
        }
        if self.mapped('account_move'):
            report = self.env.ref('point_of_sale.pos_invoice_report')._render_qweb_pdf(self.ids[0])
            filename = name + '.pdf'
            attachment = self.env['ir.attachment'].create({
                'name': filename,
                'type': 'binary',
                'datas': base64.b64encode(report[0]),
                'res_model': 'pos.order',
                'res_id': self.ids[0],
                'mimetype': 'application/x-pdf'
            })
            mail_values['attachment_ids'] += [(4, attachment.id)]
        mail = self.env['mail.mail'].sudo().create(mail_values)
        mail.send()

    def _prepare_invoice_line_tax(self, order_line, res):
        fpos = order_line.order_id.fiscal_position_id
        tax_ids_after_fiscal_position = fpos.map_tax(order_line.tax_ids, order_line.product_id, order_line.order_id.partner_id)
        price = res['price_unit'] * (1 - (res['discount'] or 0.0) / 100.0)
        taxes = tax_ids_after_fiscal_position.compute_all(price, order_line.order_id.pricelist_id.currency_id, order_line.qty, product=order_line.product_id, partner=order_line.order_id.partner_id)    
        return {
            'price_subtotal_incl': taxes['total_included'],
            'price_subtotal': taxes['total_excluded'],
            'price_unit': price,
        }

    def _prepare_invoice_line(self, order_line):
        config_id = self.config_id
        if config_id.iface_tipproduct and config_id.tip_product_id == order_line.product_id:
            return {}
        if order_line.price_unit <= 0:
            return {}
        res = super(PosOrder, self)._prepare_invoice_line(order_line=order_line)
        wh_loc_id = config_id.picking_type_id.warehouse_id
        analytic_loc_id = wh_loc_id and wh_loc_id.account_analytic_id and wh_loc_id.account_analytic_id.id or False        
        res['price_unit'] = order_line.price_subtotal / order_line.qty
        res['analytic_account_id'] = analytic_loc_id
        return res

    def _prepare_invoice_vals(self):
        vals = super(PosOrder, self)._prepare_invoice_vals()
        invoice_line_ids = []
        for line in self.lines:
            vals_line = self._prepare_invoice_line(line)
            if vals_line:
                invoice_line_ids.append( (0, None, vals_line) )

        certificate_date = self.env['l10n_mx_edi.certificate'].sudo().get_mx_current_datetime()
        vals['invoice_line_ids'] = invoice_line_ids
        vals['invoice_date'] = certificate_date.date()
        return vals

    def action_auto_invoice(self, partner_id=False):
        company_id = request.env.ref('__export__.res_company_12_276637f1', raise_if_not_found=False)
        InvoiceModel = request.env['account.move'].with_user(SUPERUSER_ID)
        inv_id = False
        self.write({
            'partner_id':partner_id.id,
        })
        inv_datas = self.action_pos_order_invoice()
        self.env.cr.commit()
        if 'res_id' in inv_datas:
            inv_id = InvoiceModel.browse( inv_datas['res_id'] ).with_company(company_id)

            certificate_date = self.env['l10n_mx_edi.certificate'].sudo().with_company(company_id).get_mx_current_datetime()
            issued_address = inv_id._get_l10n_mx_edi_issued_address()
            tz = inv_id._l10n_mx_edi_get_cfdi_partner_timezone(issued_address)
            tz_force = self.env['ir.config_parameter'].sudo().get_param('l10n_mx_edi_tz_%s' % inv_id.journal_id.id, default=None)
            if tz_force:
                tz = timezone(tz_force)
            inv_id.write({
                'l10n_mx_edi_payment_policy': 'PUE',
                'l10n_mx_edi_usage': partner_id.l10n_mx_edi_usage,
                'invoice_date': certificate_date.date(),
                'l10n_mx_edi_post_time': fields.Datetime.to_string(datetime.now(tz))
            })
            self.env.cr.commit()
            # inv_id.with_context(check_move_validity=False)._onchange_invoice_date()
            if not inv_id.l10n_mx_edi_cfdi_uuid:
                inv_id.action_process_edi_web_services()
                self.env.cr.commit()
            if not inv_id.l10n_mx_edi_cfdi_uuid:
                inv_id.action_process_edi_web_services()
                self.env.cr.commit()
        return {'inv_id': inv_id}
