# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from itertools import groupby

import logging
_logger = logging.getLogger(__name__)


def grouplines(self, ordered_lines, sortkey):
    """Return lines from a specified invoice or sale order grouped by category"""
    grouped_lines = []
    for key, valuesiter in groupby(ordered_lines, None):
        group = {}
        group['lines'] = list(v for v in valuesiter)
        key = group['lines'][0].layout_category_id

        if 'subtotal' in key and key.subtotal is True:
            group['subtotal'] = sum(line.price_subtotal for line in group['lines'])

        for line in group['lines']:
            if line.product_uom_qty == 0.0:
                group['lines'].remove(line)
                group['category'] = ''
            else:
                group['category'] = line.layout_category_id

        grouped_lines.append(group)

    return grouped_lines


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    internal_cat = fields.Char(related='product_id.categ_id.name',
                               store='True', string='Internal Category', readonly=True)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    print_internal_ref = fields.Boolean(string='Print Internal Reference', help="Prints Art.-Nr. in the report")

    beneficiary = fields.Many2one('res.partner', string='Beneficiary')

    # Replace Template on Print Button
    def print_quotation_grimm(self):
        self.filtered(lambda s: s.state == 'draft').write({'state': 'sent'})
        return self.env['report'].get_action(self, 'grimm_reports.report_saleorder_grimm')

    def print_delivery_notice(self):
        self.filtered(lambda s: s.state == 'sale').write({'state': 'done'})
        self.write({'state': 'done'})
        return self.env['report'].get_action(self, 'grimm_reports.report_delivery_notice_grimm')

    def print_project_description(self):
        self.filtered(lambda s: s.state == 'sale').write({'state': 'done'})
        self.write({'state': 'done'})
        return self.env['report'].get_action(self, 'grimm_reports.report_project_description_grimm')

    def action_dn_sent(self):
        """ Open a window to compose an email, with the delivery notice template
            message loaded by default
        """
        self.ensure_one()
        template = self.env.ref('grimm_reports.email_template_delivery_notice', False)
        compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
        ctx = dict(
            default_model='sale.order',
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template.id,
            default_composition_mode='comment',
            mark_invoice_as_sent=True,
            _send_delivery_notice=True,
            #custom_layout="sale.mail_template_data_notification_email_sale_order",
        )
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

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        """
        mod search to search orders ready to confirm
        """
        query = """
            SELECT
              _so.id                 AS sale_order_id,
              count(DISTINCT _po.id) AS purchase_number,
              count(DISTINCT _ai.id) AS invoice_numnber
            FROM sale_order _so
              INNER JOIN purchase_order _po ON position(_so.name IN _po.origin) > 0
              INNER JOIN purchase_order_line _pol ON _po.id = _pol.order_id
              LEFT JOIN account_invoice_line _ail ON _pol.id = _ail.purchase_line_id
              LEFT JOIN account_invoice _ai ON _ail.invoice_id = _ai.id AND
                                               _ai.type = 'in_invoice' AND _ai.state IN ('open', 'paid')
              INNER JOIN account_invoice _proforma ON _so.name = _proforma.origin
            WHERE _so.state IN ('sale', 'done')
                  AND _proforma.state IN ('proforma', 'proforma2')
            GROUP BY _so.id
            HAVING count(DISTINCT _po.id) = count(DISTINCT _ai.id)"""

        if self._context.get("__ready_to_confirm", 0):
            self._cr.execute(query)
            results = self._cr.fetchall()
            ids = []
            for row in results:
                ids.append(row[0])
            # self._context.pop(u"ready_to_confirm")
            args.append(("id", "in", ids))
        ret = super(SaleOrder, self).search(args, offset=offset,
                                            limit=limit, order=order, count=count)

        return ret

    def sale_layout_lines(self, order_id=None):
        """
        Returns order lines from a specified sale ordered by
        sale_layout_category sequence. Used in sale_layout module.

        :Parameters:
            -'order_id' (int): specify the concerned sale order.
        """
        ordered_lines = self.browse(order_id).order_line
        sortkey = lambda x: x.layout_category_id if x.layout_category_id else ''

        return grouplines(self, ordered_lines, sortkey)
