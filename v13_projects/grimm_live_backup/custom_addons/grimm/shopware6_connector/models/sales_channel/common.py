# -*- coding: utf-8 -*-
# © 2013-2017 Guewen Baconnier,Camptocamp SA,Akretion
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from datetime import datetime, timedelta
from odoo import models, fields, api
from odoo.addons.component.core import Component
import logging
from datetime import datetime
from datetime import timedelta
_logger = logging.getLogger(__name__)

IMPORT_DELTA_BUFFER = 30


class SalesChannelShopware6(models.Model):
    _name = 'sales.channel'
    _inherit = ['shopware6.binding']
    _description = 'Shopware Sales Channel'
    _parent_name = 'backend_id'


    name = fields.Char(required=True, readonly=True)
    host = fields.Char(readonly=True)
    lang_id = fields.Many2one(comodel_name='res.lang', string='Language')
    shopware_currency_id = fields.Char(readonly=True)

    '''
    import_partners_from_date = fields.Datetime(
        string='Import partners from date',
    )
    product_binding_ids = fields.Many2many(
        comodel_name='shopware.product.product',
        string='Shopware Products',
        readonly=True,
    )
    '''
    import_orders_from_date = fields.Datetime(
        string='Import sale orders from date',
        help='do not consider non-imported sale orders before this date. '
             'Leave empty to import all sale orders',
    )
    no_sales_order_sync = fields.Boolean(
        string='No Sales Order Synchronization',
        help='Check if the shop is active in Shopware '
             'but its sales orders should not be imported.',
    )
    specific_fiscal_position_id = fields.Many2one(
        comodel_name='account.fiscal.position',
        string='Specific fiscal position',
        help='If specified, this fiscal position will be used to fill the '
             'field fiscal position on the sale order created by the connector.'
             'The value can also be specified on shop or the shop or the '
             'shop view.'
    )
    account_analytic_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Analytic account',
        compute='_get_account_analytic_id',
    )
    fiscal_position_id = fields.Many2one(
        comodel_name='account.fiscal.position',
        string='Fiscal position',
        compute='_get_fiscal_position_id',
    )

    @property
    def _parent(self):
        return getattr(self, self._parent_name)

    def _get_account_analytic_id(self):
        for this in self:
            this.account_analytic_id = (
                    this.specific_account_analytic_id or
                    this._parent.account_analytic_id)

    def _get_fiscal_position_id(self):
        for this in self:
            this.fiscal_position_id = (
                    this.specific_fiscal_position_id or
                    this._parent.fiscal_position_id)


    def import_sale_orders(self):
        import_start_time = datetime.now()
        hours_diff = 0
        for shop in self:
            if shop.no_sales_order_sync:
                _logger.debug("The storeview '%s' is active in Shopware "
                              "but is configured not to import the "
                              "sales orders", shop.name)
                continue

            sale_binding_model = self.env['shopware6.sale.order']
            backend = shop.backend_id
            if shop.import_orders_from_date:
                from_date = (shop.import_orders_from_date + timedelta(hours=hours_diff)).isoformat()
            else:
                from_date = None
            delayable = sale_binding_model.with_delay(priority=1)

            filter_list = []
            fields_list = {
                "order": ["id", "orderNumber"]
            }
            filter_list.append({
                'field': 'salesChannelId',
                'type': 'equals',
                'value': shop.shopware6_id,
            })
            if from_date is not None:
                filter_list.append(
                    {
                        "type":"range",
                        "field":"createdAt",
                        "parameters":{
                            "gt":from_date,
                            "lt":(import_start_time + timedelta(hours=hours_diff)).isoformat()
                        }
                    }
                )
            else:
                filter_list.append(
                    {
                        "type": "range",
                        "field": "createdAt",
                        "parameters": {
                            "lt": (import_start_time + timedelta(hours=hours_diff)).isoformat()
                        }
                    }
                )
            delayable.import_batch(backend, filters={"filter": filter_list, "includes":fields_list})
        next_time = import_start_time - timedelta(seconds=IMPORT_DELTA_BUFFER)
        next_time = fields.Datetime.to_string(next_time)
        self.write({'import_orders_from_date': next_time})
        return True

class Shopware6SalesChannelAdapter(Component):
    _name = 'shopware6.sales.channel.adapter'
    _inherit = 'shopware6.adapter'
    _apply_on = 'sales.channel'

    _shopware_uri = 'api/v3/sales-channel/'

    def _call(self, method, api_call, arguments=None):
        try:
            return super(Shopware6SalesChannelAdapter, self)._call(method, api_call, arguments)
        except xmlrpc.client.Fault as err:
            # this is the error in the Shopware API
            # when the product does not exist
            if err.faultCode == 101:
                raise IDMissingInBackend
            else:
                raise

    def search(self, filters=None):
        """ Search records according to some criterias
        and returns a list of ids

        :rtype: list
        """
        return self._call('get','%s' % self._shopware_uri,[filters] if filters else [{}])

    def read(self, id, attributes=None):
        """ Returns the information of a record

        :rtype: dict
        """
        return self._call('get', '%s%s' % (self._shopware_uri,id), [{}])
