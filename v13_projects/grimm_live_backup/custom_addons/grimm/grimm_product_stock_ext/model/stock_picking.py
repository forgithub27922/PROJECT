from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        count = 0
        if self.sale_id and self.sale_id.order_line:
            for line in self.sale_id.order_line:
                _logger.info('Check if equal ' + str(line.product_uom_qty) + '==' + str(line.qty_delivered))
                if line.product_uom_qty == line.qty_delivered:
                    if line.route_id.id != 6 and line.product_id.type == 'product':
                        count += 1
            if count > 0:
                message = _('Sales order %s is fully delivered' % self.sale_id.name)
                self.sale_id.message_post(subject=_('Delivery Successful'), body=message)
                _logger.info("[Delivery Successful]: %s" % message)

        return res
