# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2016 Openfellas (http://openfellas.com) All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly advised to contract support@openfellas.com
#
##############################################################################

from openerp import models, fields, api


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    exported_to_datev = fields.Boolean(string='Exported to Datev', default=False, copy=False, track_visibility='onchange')

    delivery_date = fields.Date(string='Delivery Date', track_visibility='onchange')
    delivery_date_start = fields.Date(string='Delivery Start Date', track_visibility='onchange')
    delivery_date_end = fields.Date(string='Delivery End Date', track_visibility='onchange')

    def _get_invoice_refunded_filter(self):
        """ Hook to set filter default search by origin """
        if not self.invoice_origin:
            return False
        origin_splited = list(set(self.invoice_origin.split(',')))
        origin_list = []
        origin_list.extend(origin_splited)
        filter = [('name', 'in', origin_list)]
        return filter


    def _get_invoices_refunded(self):
        if not self.type in ('out_refund', 'in_refund'):
            return False
        filter = self._get_invoice_refunded_filter()
        if not filter:
            return False
        invoices = self.search(filter)
        if not invoices:
            return False
        sum = 0.00
        for invoice in invoices:
            sum += round(invoice.amount_total or 0.00, 2)
        if sum != self.amount_total:
            return False
        return invoices



class AccountInvoiceLine(models.Model):
    _inherit = 'account.move.line'

    def _get_bu_code_tax(self):
        """ Hook to calculate bu_code depanding on taxes """
        self.ensure_one()
        bu_code = '0'
        if self.tax_ids and self.tax_ids[0]:
            bu_code = '%s' % (self.tax_ids[0].tax_code or '0',)
        return bu_code

    def _get_code_for_refunds(self):
        """ Hook to calculate bu_code depanding on taxes """
        self.ensure_one()
        bu_code_for_refunds = ''
        if self.tax_ids and self.tax_ids[0]:
            bu_code_for_refunds = '%s' % (self.tax_ids[0].code_for_refunds or '',)
        return bu_code_for_refunds

    def _calculate_bu_code(self):
        self.ensure_one()
        bu_code = '%s' % (self._get_bu_code_tax(),)
        invoices = self.move_id and self.move_id._get_invoices_refunded() or False
        if invoices:
            bu_code_for_refunds = '%s' % (self._get_code_for_refunds(),)
            bu_code = '%s%s' % (bu_code_for_refunds, bu_code)
        return bu_code





