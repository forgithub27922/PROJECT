from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging
import re

_logger = logging.getLogger(__name__)


class AccInv(models.Model):
    _inherit = 'account.move'

    def vendorbill_fix_action(self, active_ids=False, context=False):
        accounts = self.browse(active_ids)
        for rec in accounts:
            source = rec.get_source_document()
            if source:
                if source["res_model"] == "purchase.order":
                    source_rec = self.env[source["res_model"]].browse(source["res_id"])
                    invoices_true = source_rec.mapped('order_line.invoice_lines.move_id')
                    invoices_extra = self.search([('invoice_origin', 'like', source_rec.name), ('type', 'in', ['in_invoice', 'in_refund'])])
                    source_rec.invoice_ids = invoices_true + invoices_extra
                    source_rec.invoice_count = len(set(invoices_true + invoices_extra))



    @api.model
    def vendorbill_fix(self):
        AccInv = self.search([('type', '!=', 'Customer Invoice')])
        for rec in AccInv:
            if rec not in [inv for inv in rec.purchase_id_copy.invoice_ids]:
                if rec.purchase_id_copy:
                    rec.purchase_id_copy.invoice_count += 1
                    inv_ids = [inv.id for inv in rec.purchase_id_copy.invoice_ids]
                    inv_ids.append(rec.id)
                    rec.purchase_id_copy.invoice_ids = [(6, 0, inv_ids)]
                    _logger.info('[CRON JOB] Fixing data errors temporarily of account.invoice: ' + str(rec.purchase_id_copy.invoice_ids))

    reference = fields.Char(string='Vendor Reference', copy=False,
                            help="The partner reference of this invoice.", readonly=True,
                            states={'draft': [('readonly', False)]}, required=True)

    @api.constrains('ref')
    def _validate_reference(self):
        for rec in self:
            if rec.ref and not re.search("^[a-zA-Z0-9$&%*\+\-/]{1,12}$", rec.ref) and rec.type == 'in_invoice':
                raise ValidationError(
                    'Die eingegebene Lieferantenreferenz erfüllt nicht die folgenden Kriterien:\n' + _(
                        'digits 0 1 2 3 4 5 6 7 8 9\ncapital letters A B C...Z\nsmall letters a b c... z\nspecial characters $ & % *+ - /\nlength	max. 12 Zeichen'))
