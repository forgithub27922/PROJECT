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


class ShopwareShop(models.Model):
    _name = 'shopware.shop'
    _inherit = ['shopware.binding']
    _description = 'Shopware Shop'
    _parent_name = 'backend_id'

    _order = 'sort_order ASC, id ASC'

    name = fields.Char(required=True, readonly=True)
    host = fields.Char(readonly=True)
    template_id = fields.Char(readonly=True)
    enabled = fields.Boolean(string='Enabled', readonly=True)
    secure = fields.Boolean(string='Secure', readonly=True)
    sort_order = fields.Integer(string='Sort Order', readonly=True)
    lang_id = fields.Many2one(comodel_name='res.lang', string='Language')
    import_partners_from_date = fields.Datetime(
        string='Import partners from date',
    )
    '''
    product_binding_ids = fields.Many2many(
        comodel_name='shopware.product.product',
        string='Shopware Products',
        readonly=True,
    )
    '''
    send_picking_done_mail = fields.Boolean(
        string='Send email notification on picking done',
        help="Does the picking export/creation should send "
             "an email notification on Shopware side?",
    )
    send_invoice_paid_mail = fields.Boolean(
        string='Send email notification on invoice validated/paid',
        help="Does the invoice export/creation should send "
             "an email notification on Shopware side?",
    )
    create_invoice_on = fields.Selection(
        selection=[('open', 'Validate'),
                   ('paid', 'Paid')],
        string='Create invoice on action',
        default='paid',
        required=True,
        help="Should the invoice be created in Shopware "
             "when it is validated or when it is paid in OpenERP?\n"
             "This only takes effect if the sales order's related "
             "payment method is not giving an option for this by "
             "itself. (See Payment Methods)",
    )
    section_id = fields.Many2one(comodel_name='crm.team',  # In odoo version 8 its comodel_name was 'crm.case.section'
                                 string='Sales Team')
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
    catalog_price_tax_included = fields.Boolean(string='Prices include tax')
    specific_account_analytic_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Specific analytic account',
        help='If specified, this analytic account will be used to fill the '
             'field on the sale order created by the connector. The value can '
             'also be specified on shop or the shop or the shop view.'
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

    def import_partners(self):
        # session = ConnectorSession(self.env.cr, self.env.uid,
        # context=self.env.context)
        import_start_time = datetime.now()
        for shop in self:
            backend_id = shop.backend_id.id
            if shop.import_partners_from_date:
                from_string = fields.Datetime.from_string
                from_date = from_string(shop.import_partners_from_date)
            else:
                from_date = None
            partner_import_batch.delay(
                'shopware.res.partner', backend_id,
                {'shopware_shop_id': shop.shopware_id,
                 'from_date': from_date,
                 'to_date': import_start_time})
        # Records from Shopware are imported based on their `created_at`
        # date.  This date is set on Shopware at the beginning of a
        # transaction, so if the import is run between the beginning and
        # the end of a transaction, the import of a record may be
        # missed.  That's why we add a small buffer back in time where
        # the eventually missed records will be retrieved.  This also
        # means that we'll have jobs that import twice the same records,
        # but this is not a big deal because they will be skipped when
        # the last `sync_date` is the same.
        next_time = import_start_time - timedelta(seconds=IMPORT_DELTA_BUFFER)
        next_time = fields.Datetime.to_string(next_time)
        self.write({'import_partners_from_date': next_time})
        return True

    def import_sale_orders(self):
        import_start_time = datetime.now()
        for shop in self:
            if shop.no_sales_order_sync:
                _logger.debug("The storeview '%s' is active in Shopware "
                              "but is configured not to import the "
                              "sales orders", shop.name)
                continue

            user = self.env['res.users'].browse(self.env.uid)

            sale_binding_model = self.env['shopware.sale.order']
            backend = shop.backend_id
            if shop.import_orders_from_date:
                from_date = (datetime.strptime(str(shop.import_orders_from_date), '%Y-%m-%d %H:%M:%S') + timedelta(hours=0)).isoformat()
            else:
                from_date = None
            delayable = sale_binding_model.with_delay(priority=1)

            filter_list = []
            filter_list.append({
                'property': 'shopId',
                'expression': '=',
                'value': shop.shopware_id,
            })
            filter_list.append({
                'property': 'status',
                'expression': '!=',
                'value': -1,
            })
            if from_date is not None:
                filter_list.append({
                    'property': 'orderTime',
                    'expression': '>=',
                    'value': from_date
                })
            if import_start_time is not None:
                filter_list.append({
                    'property': 'orderTime',
                    'expression': '<=',
                    'value': (import_start_time + timedelta(hours=1)).isoformat()
                })
            _logger.info("Final prepared filters for sale order is ===> %s"%filter_list)
            delayable.import_batch(backend, filters=filter_list)
        next_time = import_start_time - timedelta(seconds=IMPORT_DELTA_BUFFER)
        next_time = fields.Datetime.to_string(next_time)
        self.write({'import_orders_from_date': next_time})
        return True

class ShopwareShopAdapter(Component):
    _name = 'shopware.shop.adapter'
    _inherit = 'shopware.adapter'
    _apply_on = 'shopware.shop'

    _shopware_uri = 'shops/'

    def _call(self, method, api_call, arguments=None):
        try:
            return super(ShopwareShopAdapter, self)._call(method, api_call, arguments)
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
