# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Forecast(models.Model):
    _inherit = 'product.template'

    forecast_triplet = fields.Html('Forecast', compute='_concat_forecast_triplet', help="<b><span style='color:#00b8d9;'>Available quantity</span> (<span style='color:#36b37e;'>physical stock</span><span style='color:#ff5630'>-open customer deliveries</span><span style='color:#ff991f'> + planned order receipts</span>)</b>")

    def _get_lang_specific_format(self,value):
        lang_obj = self.env["res.lang"].search([('code', '=', self._context.get("lang", "en_US"))])
        if lang_obj:
            return lang_obj.format("%.2f", value, grouping=True, monetary=False)
        return str(value)

    def _concat_forecast_triplet(self):
        for rec in self:
            avail_color = "#00b8d9"
            if rec.virtual_available < 0:
                avail_color = "#FF0000" #Added RED color if avail quantity is less than zero.
            rec.forecast_triplet = "<b><span style='color:%s;'>%s</span></b> (<span style='color:#36b37e;'>%s</span><span style='color:#ff5630'>-%s</span><span style='color:#ff991f'>+%s</span>)" % (avail_color, self._get_lang_specific_format(rec.virtual_available), self._get_lang_specific_format(rec.qty_available), self._get_lang_specific_format(rec.outgoing_qty), self._get_lang_specific_format(rec.incoming_qty))


class PricelistOrder(models.Model):
    _inherit = 'product.pricelist'

    def _get_default_value(self):
        return self.search([], order='sequence desc', limit=1).sequence + 1

    sequence = fields.Integer(default=_get_default_value)

