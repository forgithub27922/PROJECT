# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)

class AccountInvoiceSend(models.TransientModel):
    _inherit = 'account.invoice.send'

    @api.onchange("partner_ids")
    def _get_per_post_message(self):
        self.per_post_message = ""
        for record in self:
            want_post = record.partner_ids.filtered(lambda rec: rec.invoice_by_post == True).mapped("display_name")
            if want_post:
                record.per_post_message = "<div class='alert alert-danger' role='alert'>Kunde wünscht postalischen Versand. <b>%s</b> </div>" % (
                    ", ".join(want_post))
            else:
                record.per_post_message = ""

class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    per_post_message = fields.Html("Need to send by post", readonly=True, store=False, compute="_get_per_post_message_compute")

    @api.depends("partner_ids")
    def _get_per_post_message_compute(self):
        self.per_post_message = ""
        for record in self:
            want_post = record.partner_ids.filtered(lambda rec: rec.invoice_by_post == True).mapped("display_name")
            if want_post:
                record.per_post_message = "<div class='alert alert-danger' role='alert'>Kunde wünscht postalischen Versand. <b>%s</b> </div>"%(", ".join(want_post))
            else:
                record.per_post_message = ""

class InvoiceEmail(models.Model):
    _inherit = 'res.partner'

    invoice_email = fields.Char(string='Invoice Email')
    leitweg_id = fields.Char(string='Leitweg-ID')
    invoice_by_post = fields.Boolean(string='Rechnung per Post')


    def get_partner_ref(self):
        '''
        with this method we can get the partner ref.
        :return:
        '''
        self.ensure_one()
        parent_partner = self
        while parent_partner.parent_id:
            parent_partner = parent_partner.parent_id
        return parent_partner.ref

    def name_get(self):
        res = []
        for partner in self:
            name = partner.name or ''
            if partner.company_name or partner.parent_id:
                if not name and partner.type in ['invoice', 'delivery', 'other']:
                    name = dict(self.fields_get(['type'])['type']['selection'])[partner.type]
                if not partner.is_company:
                    name = "%s, %s" % (partner.commercial_company_name or partner.parent_id.name, name)
            if self._context.get('show_address_only'):
                name = partner._display_address(without_company=True)
            if self._context.get('show_address'):
                name = name + "\n" + partner._display_address(without_company=True)
            name = name.replace('\n\n', '\n')
            name = name.replace('\n\n', '\n')
            if self._context.get('active_model', "") == "account.move" and partner.invoice_email:
                name = "%s <%s>" % (name, partner.invoice_email)
            elif self._context.get('show_email') and partner.email:
                name = "%s <%s>" % (name, partner.email)
            if self._context.get('html_format'):
                name = name.replace('\n', '<br/>')
            res.append((partner.id, name))
        return res