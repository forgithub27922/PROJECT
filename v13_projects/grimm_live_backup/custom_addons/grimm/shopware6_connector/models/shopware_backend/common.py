# -*- coding: utf-8 -*-
# © 2013 Guewen Baconnier,Camptocamp SA,Akretion
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import Warning as UserError
from ...components.backend_adapter import Shopware6API, Shopware6Location
from odoo.addons.connector.models import checkpoint

#from .partner import partner_import_batch
#from .sale import sale_order_import_batch

from contextlib import contextmanager

_logger = logging.getLogger(__name__)

IMPORT_DELTA_BUFFER = 30  # seconds

class ShopwareToken(models.Model):
    _name = 'shopware6.token'
    _description = 'Shopware6 Token'

    token_type = fields.Char(string='Token Type', readonly=True)
    access_token = fields.Char(string='Access Token', readonly=True)
    refresh_token = fields.Char(string='Refresh Token', readonly=True)
    expires_in = fields.Integer(string='Expires in (Seconds)', readonly=True)

    def is_token_expired(self, ):
        '''
        Here we set 10 second as buffer time for processing. Ex. if our token is going to expired in 600 seconds then we will
        consider 590 seconds only.
        :param vals:
        :return: True or False
        '''
        buffer_second = 10
        current_time = datetime.now()
        result = self.write_date + timedelta(seconds=(self.expires_in-buffer_second))
        return True if result < current_time else False


class Shopware6Backend(models.Model):
    _name = 'shopware6.backend'
    _description = 'Shopware6 Backend'
    _inherit = 'connector.backend'

    _backend_type = 'shopware6'

    @api.model
    def _get_stock_field_id(self):
        field = self.env['ir.model.fields'].search(
            [('model', '=', 'product.product'),
             ('name', '=', 'virtual_available')],
            limit=1)
        return field

    name = fields.Char(string='Name', required=True)
    version = fields.Char(string='Version', readonly=True)
    tax_mapping_ids = fields.One2many('shopware6.tax', 'backend_id', string='Shopware6 tax mappings')
    payment_mode_mapping_ids = fields.One2many('shopware6.account.payment.mode', 'backend_id', string='Shopware6 Payment mappings')
    media_ids = fields.One2many('media.folder', 'shopware_backend_id', string='Shopware6 Media')
    location = fields.Char(
        string='Location',
        required=True,
        help="Url to shopware6 application",
    )
    username = fields.Char(
        string='Username',
        help="Webservice user",
    )
    token = fields.Char(
        string='API key',
        help="Webservice API key",
    )
    client_id = fields.Char(
        string='Client ID',
        help="Webservice user",
    )
    client_secret = fields.Char(
        string='Client Secret',
        help="Webservice client secret key",
    )
    is_print_log = fields.Boolean(
        string='Log API call?',
        help="It will log api call in logger file.",
    )
    sale_prefix = fields.Char(
        string='Sale Prefix',
        help="A prefix put before the name of imported sales orders.\n"
             "For instance, if the prefix is 'mag-', the sales "
             "order 100000692 in Shopware6, will be named 'mag-100000692' "
             "in OpenERP.",
    )

    warehouse_id = fields.Many2one(
        comodel_name='stock.warehouse',
        string='Warehouse',
        help='Warehouse used to compute the '
             'stock quantities.',
    )
    token_info_id = fields.Many2one(
        comodel_name='shopware6.token',
        string='Token Info',
        help='Here we stored token information like expiry date time.',
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
    sales_channel_ids = fields.One2many(
        comodel_name='sales.channel',
        inverse_name='backend_id',
        string='Sales Channel',
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
    default_media_folder_id = fields.Many2one(
        comodel_name='media.folder',
        string='Default Folder to store media',
        help='Default folder to store all media from Odoo.',
    )

    # TODO? add a field `auto_activate` -> activate a cron
    import_products_from_date = fields.Datetime(
        string='Import products from date',
    )
    import_categories_from_date = fields.Datetime(
        string='Import categories from date',
    )
    import_partner_from_date = fields.Datetime(
        string='Import Partner from date',
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
        comodel_name='shopware6.product.product',
        inverse_name='backend_id',
        string='Shopware6 Products',
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

    shopware6_currency_id = fields.Char('Shopware6 Currency')

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

    def set_token_info(self, vals):
        '''
        Here we set token information of shopware6 backend like when token will expires, token data etc.
        :param vals:
        :return:
        '''
        self.ensure_one()
        token_id = self.env["shopware6.token"].sudo().create(vals)
        self.token_info_id = token_id.id

    def get_shopware_version(self):
        self.ensure_one()
        try:
            with self.work_on("shopware6.version") as work:
                importer = work.component(usage='record.importer')
                version_info = importer.backend_adapter.get_version()
                self.version = version_info.get("version")
                currency_info = importer.backend_adapter.get_currency().get("data")
                self.shopware6_currency_id = currency_info[0].get("id", "")
                return {
                    'effect': {
                        'fadeout': 'slow',
                        'message': _(
                            "Fetched Shopware version <b>%s</b> with <br/><b>%s</b>.!" % (self.name, self.location)),
                        'type': 'rainbow_man',
                    }
                }

        except Exception as e:
            raise UserError(
                _(u"Check your configuration, we can't get the data. "
                  u"Here is the error:\n%s") %
                str(e))


    def check_allowed_fields(self, model_name, fields):
        for backend in self:
            field_list = []
            model_id = self.env["ir.model"].search([('model', '=', model_name)], limit=1)
            for field in model_id.field_id.filtered(lambda r: r.update_shopware6_trigger == True):
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
            if hasattr(record, '_prepare_shopware6_specific_binding_vals'):
                binding_vals.update(record._prepare_shopware6_specific_binding_vals(self))
            res = self.env[record[bindings_field_name]._name].create(binding_vals)
        else:
            res = existing_binds

        return res

    @contextmanager
    def work_on(self, model_name, **kwargs):
        self.ensure_one()
        odoo_location = Shopware6Location(
            self.location,
            self.client_id,
            self.client_secret,
            self,
        )
        with Shopware6API(odoo_location) as shopware6_api:
            _super = super(Shopware6Backend, self)
            with _super.work_on(
                    model_name, shopware6_api=shopware6_api, **kwargs) as work:
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
        self.ensure_one()
        try:
            # session = ConnectorSession.from_env(self.env)
            for backend in self:
                for model in ['sales.channel','shopware6.tax','shopware6.account.payment.mode','shopware6.media.folder']:
                    self.env[model].with_delay().import_batch(backend)
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': _("Successfully synced <b>%s</b> with <br/><b>%s</b>.!"%(self.name,self.location)),
                    'type': 'rainbow_man',
                }
            }
        except Exception as e:
            # _logger.error(e.message, exc_info=True)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Warning!'),
                    'message': _(u"Check your configuration, we can't get the data. "u"Here is the error:\n%s") %str(e),
                    'sticky': True,
                }
            }


    def import_partners(self):
        """ Import partners from all shops """
        self._import_from_date('shopware6.res.partner',
                               'import_partner_from_date')
        return True

    def import_sale_orders(self):
        """ Import sale orders from all shop views """
        shop_obj = self.env['sales.channel']
        shops = shop_obj.search([('backend_id', 'in', self.ids)])
        shops.import_sale_orders()
        return True

    def import_customer_groups(self):
        # session = ConnectorSession(self.env.cr, self.env.uid,
        # context=self.env.context)
        for backend in self:
            backend.check_shopware_structure()
            import_batch.delay('shopware6.res.partner.category',
                               backend.id)

        return True

    def add_checkpoint(self, record):
        self.ensure_one()
        record.ensure_one()
        return checkpoint.add_checkpoint(self.env, record._name, record.id,
                                         self._name, self.id)

    def _import_from_date(self, model, from_date_field):
        import_start_time = datetime.now()

        field_name = 'updatedAt' if model == 'shopware6.product.category' else 'createdAt'
        for backend in self:
            from_date = getattr(backend, from_date_field)
            from_date = (from_date if from_date else import_start_time + timedelta(hours=0)).isoformat()
            #?query[0][query][type]=equals&query[0][query][field]=id&query[0][query][value]=7928e054212543479493fd97d33881dd
            if not from_date:
                from_date = None
            filter_list = []
            filter_list.append({
                    'field': field_name,
                    'type': 'range',
                    'parameters':{"gte": from_date}
                })

            query_string = ""
            for index,filt in enumerate(filter_list): #TODO this logic is static only for 2 inner items
                for k,v in filt.items():
                    if type(v) == type({}):
                        for key, val in v.items():
                            query_string += "query[%s][query][%s][%s]=%s&" % (index, k, key, val)
                    else:
                        query_string += "query[%s][query][%s]=%s&"%(index,k,v)
            print("query string is ===> ", query_string)
            self.env[model].with_delay().import_batch(backend, filters=query_string)
        next_time = import_start_time - timedelta(seconds=IMPORT_DELTA_BUFFER)
        next_time = fields.Datetime.to_string(next_time)
        self.write({from_date_field: next_time})

    def import_product_categories(self):
        self._import_from_date('shopware6.product.category',
                               'import_categories_from_date')
        return True

    def import_articles(self):
        self._import_from_date('shopware6.article',
                               'import_products_from_date')
        return True

    def _domain_for_update_product_stock_qty(self):
        return [
            ('backend_id', 'in', self.ids),
            ('type', '!=', 'service'),
            ('no_stock_sync', '=', False),
        ]

    def update_product_stock_qty(self):
        mag_product_obj = self.env['shopware6.product.product']
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
        requests / responses with Shopware6.  Used to generate test data.
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


# class ShopwareTaxMapping(models.Model):
#     _name = 'shopware6.tax.mapping'
#     _description = 'Shopware6 Tax Mapping'
#
#     tax_id = fields.Many2one('account.tax', string='Tax', required=True)
#     shopware_tax_percent = fields.Float(string='Shopware6 tax percent', required=True)
#     backend_id = fields.Many2one('shopware6.backend', string='Shopware6 backend')
#
#     _sql_constraints = [('tax_amount_backend_unique', 'unique (tax_id,shopware_tax_percent,backend_id)',
#                          'Tax mapping must be unique per backend!')]