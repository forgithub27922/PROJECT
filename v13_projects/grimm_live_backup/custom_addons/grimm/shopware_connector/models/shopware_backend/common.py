# -*- coding: utf-8 -*-
# © 2013 Guewen Baconnier,Camptocamp SA,Akretion
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import Warning as UserError
from ...components.backend_adapter import ShopwareAPI, ShopwareLocation
from odoo.addons.connector.models import checkpoint

#from .partner import partner_import_batch
#from .sale import sale_order_import_batch

from contextlib import contextmanager

_logger = logging.getLogger(__name__)

IMPORT_DELTA_BUFFER = 30  # seconds

class ShopwareTaxMapping(models.Model):
    _name = 'shopware.tax.mapping'
    _description = 'Shopware Tax Mapping'

    tax_id = fields.Many2one('account.tax', string='Tax', required=True)
    shopware_tax_percent = fields.Float(string='Shopware tax percent', required=True)
    backend_id = fields.Many2one('shopware.backend', string='Shopware backend')

    _sql_constraints = [('tax_amount_backend_unique', 'unique (tax_id,shopware_tax_percent,backend_id)',
                         'Tax mapping must be unique per backend!')]


class ShopwareBackend(models.Model):
    _name = 'shopware.backend'
    _description = 'Shopware Backend'
    _inherit = 'connector.backend'

    _backend_type = 'shopware'

    @api.model
    def select_versions(self):
        """ Available versions in the backend.

        Can be inherited to add custom versions.  Using this method
        to add a version from an ``_inherit`` does not constrain
        to redefine the ``version`` field in the ``_inherit`` model.
        """
        return [('5.5.5', '5.5+')]

    @api.model
    def _get_stock_field_id(self):
        field = self.env['ir.model.fields'].search(
            [('model', '=', 'product.product'),
             ('name', '=', 'virtual_available')],
            limit=1)
        return field

    name = fields.Char(string='Name', required=True)
    version = fields.Selection(selection='select_versions', required=True)
    tax_mapping_ids = fields.One2many('shopware.tax.mapping', 'backend_id', string='Shopware tax mappings')
    location = fields.Char(
        string='Location',
        required=True,
        help="Url to shopware application",
    )
    username = fields.Char(
        string='Username',
        help="Webservice user",
    )
    token = fields.Char(
        string='API key',
        help="Webservice API key",
    )
    sale_prefix = fields.Char(
        string='Sale Prefix',
        help="A prefix put before the name of imported sales orders.\n"
             "For instance, if the prefix is 'mag-', the sales "
             "order 100000692 in Shopware, will be named 'mag-100000692' "
             "in OpenERP.",
    )

    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Warehouse',
        help='Warehouse used to compute the '
             'stock quantities.',
    )
    default_company_id = fields.Many2one(
        comodel_name='res.company',
        string='Default company',
        help='When we import any record like Sale Orders etc will be created for this company.',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        related='warehouse_id.company_id',
        string='Default Company',
        readonly=True,
    )
    shop_ids = fields.One2many(
        comodel_name='shopware.shop',
        inverse_name='backend_id',
        string='Shop',
        #readonly=True,
    )
    default_lang_id = fields.Many2one(
        comodel_name='res.lang',
        string='Default Language',
        help="If a default language is selected, the records "
             "will be imported in the translation of this language.\n"
             "Note that a similar configuration exists "
             "for each shop.",
    )
    default_category_id = fields.Many2one(
        comodel_name='product.category',
        string='Default Product Category',
        help='If a default category is selected, products imported '
             'without a category will be linked to it.',
    )

    # TODO? add a field `auto_activate` -> activate a cron
    import_products_from_date = fields.Datetime(
        string='Import products from date',
    )
    import_categories_from_date = fields.Datetime(
        string='Import categories from date',
    )
    product_stock_field_id = fields.Many2one(
        comodel_name='ir.model.fields',
        string='Stock Field',
        default=_get_stock_field_id,
        domain="[('model', 'in', ['product.product', 'product.template']),"
               " ('ttype', '=', 'float')]",
        help="Choose the field of the product which will be used for "
             "stock inventory updates.\nIf empty, Quantity Available "
             "is used.",
    )
    '''
    product_binding_ids = fields.One2many(
        comodel_name='shopware.product.product',
        inverse_name='backend_id',
        string='Shopware Products',
        readonly=True,
    )
    '''
    account_analytic_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Analytic account',
        help='If specified, this analytic account will be used to fill the '
             'field  on the sale order created by the connector. The value can '
             'also be specified on shop or the shop or the shop view.'
    )
    fiscal_position_id = fields.Many2one(
        comodel_name='account.fiscal.position',
        string='Fiscal position',
        help='If specified, this fiscal position will be used to fill the '
             'field fiscal position on the sale order created by the connector.'
             'The value can also be specified on shop or the shop or the '
             'shop view.'
    )

    _sql_constraints = [
        ('sale_prefix_uniq', 'unique(sale_prefix)',
         "A backend with the same sale prefix already exists")
    ]

    def _prepare_default_binding_vals(self, record):
        self.ensure_one()
        return {
            'backend_id': self.id,
            'openerp_id': record.id
        }

    def check_allowed_fields(self, model_name, fields):
        for backend in self:
            field_list = []
            model_id = self.env["ir.model"].search([('model', '=', model_name)], limit=1)
            for field in model_id.field_id.filtered(lambda r: r.update_shopware_trigger == True):
                field_list.append(field.name)
            for field in fields:
                if field in field_list:
                    return True
        return False

    def create_bindings_for_model(self, record, bindings_field_name):
        self.ensure_one()
        existing_binds = record[bindings_field_name].filtered(lambda rec: rec.backend_id.id == self.id)
        if not existing_binds:
            binding_vals = self._prepare_default_binding_vals(record)
            if hasattr(record, '_prepare_specific_binding_vals'):
                binding_vals.update(record._prepare_specific_binding_vals(self))
            res = self.env[record[bindings_field_name]._name].create(binding_vals)
        else:
            res = existing_binds

        return res

    @contextmanager
    def work_on(self, model_name, **kwargs):
        self.ensure_one()
        odoo_location = ShopwareLocation(
            self.location,
            self.username,
            self.token,
        )
        with ShopwareAPI(odoo_location) as shopware_api:
            _super = super(ShopwareBackend, self)
            with _super.work_on(
                    model_name, shopware_api=shopware_api, **kwargs) as work:
                yield work

    def check_shopware_structure(self):
        """ Used in each data import.

        Verify if a shop exists for each backend before starting the import.
        """
        for backend in self:
            shops = backend.shop_ids
            if not shops:
                backend.synchronize_metadata()
        return True

    def synchronize_metadata(self):
        try:
            # session = ConnectorSession.from_env(self.env)
            for backend in self:
                for model in ['shopware.shop']:
                    self.shop_ids.unlink() # Remove old shop data before import so every sync we have latest shop data.
                    self.env[model].import_batch(backend)
            return True
        except Exception as e:
            #_logger.error(e.message, exc_info=True)
            raise UserError(
                _(u"Check your configuration, we can't get the data. "
                  u"Here is the error:\n%s") %
                str(e))

    def import_partners(self):
        """ Import partners from all shops """
        for backend in self:
            backend.check_shopware_structure()
            backend.shop_ids.import_partners()
        return True

    def import_sale_orders(self):
        """ Import sale orders from all shop views """
        shop_obj = self.env['shopware.shop']
        shops = shop_obj.search([('backend_id', 'in', self.ids)])
        shops.import_sale_orders()
        return True

    def import_customer_groups(self):
        # session = ConnectorSession(self.env.cr, self.env.uid,
        # context=self.env.context)
        for backend in self:
            backend.check_shopware_structure()
            import_batch.delay('shopware.res.partner.category',
                               backend.id)

        return True

    def add_checkpoint(self, record):
        self.ensure_one()
        record.ensure_one()
        return checkpoint.add_checkpoint(self.env, record._name, record.id,
                                         self._name, self.id)

    def _import_from_date(self, model, from_date_field):
        import_start_time = datetime.now()
        for backend in self:
            from_date = getattr(backend, from_date_field)
            from_date = (datetime.strptime(str(from_date), '%Y-%m-%d %H:%M:%S') + timedelta(hours=0)).isoformat()
            if not from_date:
                from_date = None
            filter_list = []
            filter_list.append({
                    'property': 'changed',
                    'expression': '>=',
                    'value': from_date
                })
            filter_list.append({
                    'property': 'changed',
                    'expression': '<=',
                    'value': (import_start_time + timedelta(hours=0)).isoformat()
                })
            self.env[model].with_delay().import_batch(backend, filters=filter_list)
        next_time = import_start_time - timedelta(seconds=IMPORT_DELTA_BUFFER)
        next_time = fields.Datetime.to_string(next_time)
        self.write({from_date_field: next_time})

    def import_product_categories(self):
        self._import_from_date('shopware.product.category',
                               'import_categories_from_date')
        return True

    def import_articles(self):
        self._import_from_date('shopware.article',
                               'import_products_from_date')
        return True

    def _domain_for_update_product_stock_qty(self):
        return [
            ('backend_id', 'in', self.ids),
            ('type', '!=', 'service'),
            ('no_stock_sync', '=', False),
        ]

    def update_product_stock_qty(self):
        mag_product_obj = self.env['shopware.product.product']
        domain = self._domain_for_update_product_stock_qty()
        shopware_products = mag_product_obj.search(domain)
        shopware_products.recompute_shopware_qty()
        return True

    @api.model
    def _shopware_backend(self, callback, domain=None):
        if domain is None:
            domain = []
        backends = self.search(domain)
        if backends:
            getattr(backends, callback)()

    @api.model
    def _scheduler_import_sale_orders(self, domain=None):
        self._shopware_backend('import_sale_orders', domain=domain)

    @api.model
    def _scheduler_import_customer_groups(self, domain=None):
        self._shopware_backend('import_customer_groups', domain=domain)

    @api.model
    def _scheduler_import_partners(self, domain=None):
        self._shopware_backend('import_partners', domain=domain)

    @api.model
    def _scheduler_import_product_categories(self, domain=None):
        self._shopware_backend('import_product_categories', domain=domain)

    @api.model
    def _scheduler_import_product_product(self, domain=None):
        self._shopware_backend('import_articles', domain=domain)
        # "import_articles" is name of above method to call from scheduler

    @api.model
    def _scheduler_update_product_stock_qty(self, domain=None):
        self._shopware_backend('update_product_stock_qty', domain=domain)

    def output_recorder(self):
        """ Utility method to output a file containing all the recorded
        requests / responses with Shopware.  Used to generate test data.
        Should be called with ``erppeek`` for instance.
        """
        from .unit.backend_adapter import output_recorder
        import os
        import tempfile
        fmt = '%Y-%m-%d-%H-%M-%S'
        timestamp = datetime.now().strftime(fmt)
        filename = 'output_%s_%s' % (self.env.cr.dbname, timestamp)
        path = os.path.join(tempfile.gettempdir(), filename)
        output_recorder(path)
        return path