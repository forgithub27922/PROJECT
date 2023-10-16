# -*- coding: utf-8 -*-

from odoo import models, api, fields


class MailComposeMessage(models.TransientModel):
    _inherit = 'mail.compose.message'

    def send_mail(self, auto_commit=False):
        context = self._context
        ret = super(MailComposeMessage, self).send_mail(auto_commit=auto_commit)
        if context.get('default_model') == "sale.order" and context.get('_send_delivery_notice', None):
            for row in self.env['sale.order'].search([("id", "in", context.get('active_ids', []))]):
                row.sent_dn_date = fields.datetime.now()
        return ret

    @api.model
    def default_get(self, fields):
        result = super(MailComposeMessage, self).default_get(fields)
        if result.get('body', '') == '':
            result.update({'body': "<p style='font-family: arial,helvetica,sans-serif; font-size: 16px; margin-bottom: 21px; line-height: 21px;'><br/></p>"})
        return result
