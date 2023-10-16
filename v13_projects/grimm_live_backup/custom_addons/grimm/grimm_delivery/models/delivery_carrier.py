# -*- coding: utf-8 -*-

from odoo import models, _
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    def _get_price_available(self, order):
        self.ensure_one()
        total = weight = volume = quantity = 0
        total_delivery = 0.0
        total_delivery_net = 0.0
        for line in order.order_line:
            if line.state == 'cancel':
                continue
            if line.is_delivery:
                total_delivery += line.price_total
                total_delivery_net += line.price_subtotal
            if not line.product_id or line.is_delivery:
                continue
            qty = line.product_uom._compute_quantity(line.product_uom_qty, line.product_id.uom_id)
            weight += (line.product_id.weight or 0.0) * qty
            volume += (line.product_id.volume or 0.0) * qty
            quantity += qty
        total = (order.amount_total or 0.0) - total_delivery
        total_net = (order.amount_untaxed or 0.0) - total_delivery_net
        total = order.currency_id.with_context(date=order.date_order).compute(total, order.company_id.currency_id)
        total_net = order.currency_id.with_context(date=order.date_order).compute(total_net,
                                                                                  order.company_id.currency_id)

        return self._get_price_from_picking(total, total_net, weight, volume, quantity)

    def _get_price_from_picking(self, total, total_net, weight, volume, quantity):
        price = 0.0
        criteria_found = False
        price_dict = {'price': total, 'net_price': total_net, 'volume': volume, 'weight': weight, 'wv': volume * weight,
                      'quantity': quantity}
        for line in self.price_rule_ids:
            test = safe_eval(line.variable + line.operator + str(line.max_value), price_dict)
            if test:
                price = line.list_base_price + line.list_price * price_dict[line.variable_factor]
                criteria_found = True
                break
        if not criteria_found:
            raise UserError(_("No price rule matching this order; delivery cost cannot be computed."))

        return price
