# -*- coding: utf-8 -*-


from openerp import models, fields
import odoo.addons.decimal_precision as dp


class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    def _get_task_id(self):
        for event in self:
            event.task_id = self.env['project.task'].search(
                [('meeting_id', '=', event.id)], limit=1)

    task_id = fields.Many2one(comodel_name='project.task', string='Task', compute=_get_task_id, readonly=True)

class ProductPriceHistory(models.Model):
    _name = 'product.price.history'
    _description = 'Product price history'

    def _get_default_company_id(self):
        return self._context.get('force_company', self.env.user.company_id.id)

    company_id = fields.Many2one('res.company', string='Company',
                                 default=_get_default_company_id, required=True)
    product_id = fields.Many2one('product.product', 'Product', ondelete='cascade', required=True)
    datetime = fields.Datetime('Date', default=fields.Datetime.now)
    cost = fields.Float('Cost', digits='Product Price')
    transfer_on = fields.Selection(selection=[('magento', 'Magento'), ('shopware', 'Shopware')], string='Transfer On',
                                   default='magento', required=True)

