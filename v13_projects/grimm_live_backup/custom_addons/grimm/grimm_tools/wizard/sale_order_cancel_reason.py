# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _


class SaleOrderCancelReason(models.Model): # After discussion with Tobias changed to regular model instead of Transient Model
    _name = 'sale.order.cancel.reason'
    _description = 'Quotation Reject Reason'

    name = fields.Selection(
        [('long_delivery', 'Too long delivery time'),
         ('expensive', 'We were priced too expensive'),
         ('changed_by_customer', 'Customer has made changes/exchange'),
         ('wrong_product', 'Wrong product ordered / does not fit'),
         ('not_paid', 'Customer has not paid in advance'),
         ('wrong_address', 'Billing/delivery address was not correct'),
         ('wrong_delivery', 'Wrong Delivery'),
         ('fake_test_offer', 'Test / Fake Bestellung'),
         ('other', 'Other Reason')],
        string='Select Reason', required=True)
    other_reason = fields.Text("Other Reason")
    type = fields.Char("Type")
    sale_order_ids = fields.Many2many('sale.order')
    def action_cancel_reason_apply(self):
        for order in self.sale_order_ids:
            reason = self.name
            try:
                selection = self.fields_get().get("name", {}).get("selection", []) #To get german translation of selection field value
                for sel in selection:
                    if sel[0] == self.name:
                        reason = sel[1]
                        break
            except:
                reason = self.name
            if self.name == 'other':
                reason += " : "+str(self.other_reason)

            order.cancel_reason = reason
            order.message_post(subject="Bestellung storniert", body="<strong>Bestellung storniert</strong><br/><br/>"+reason, subtype_xmlid='mail.mt_note')
            if self.type == 'order':
                order.action_cancel()
            else:
                order.action_proforma_cancel()
        return True
