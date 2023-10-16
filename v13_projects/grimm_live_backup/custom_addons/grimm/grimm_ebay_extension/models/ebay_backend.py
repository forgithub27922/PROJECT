# -*- coding: utf-8 -*-
# © 2013 Guewen Baconnier,Camptocamp SA,Akretion
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import datetime
from odoo import models, fields, api, _
_logger = logging.getLogger(__name__)




class EbayBackend(models.Model):
    _name = 'ebay.backend'
    _description = 'Ebay Backend'

    name = fields.Char(string='Name', required=True)
    active = fields.Boolean(string='Active', default=False, copy=False)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
    )
    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist', required=True)
    ebay_dev_id = fields.Char("Developer Key")
    ebay_sandbox_token = fields.Text("Sandbox Token")
    ebay_sandbox_app_id = fields.Char("Sandbox App Key")
    ebay_sandbox_cert_id = fields.Char("Sandbox Cert Key")

    ebay_prod_token = fields.Text("Production Token")
    ebay_prod_app_id = fields.Char("Production App Key")
    ebay_prod_cert_id = fields.Char("Production Cert Key")
    ebay_domain = fields.Selection([
        ('prod', 'Production'),
        ('sand', 'Sandbox'),
    ], string='Mode', default='sand', required=True)
    ebay_currency = fields.Many2one("res.currency", string='Currency',
                                    domain=[('ebay_available', '=', True)], required=True)
    ebay_country = fields.Many2one("res.country", domain=[('ebay_available', '=', True)],
                                   string="Country")
    ebay_site = fields.Many2one("ebay.site", string="eBay Website")
    ebay_zip_code = fields.Char(string="Zip")
    ebay_location = fields.Char(string="Location")
    ebay_out_of_stock = fields.Boolean("Out Of Stock", default=False)
    ebay_sales_team = fields.Many2one("crm.team", string="Sales Channel")
    ebay_gallery_plus = fields.Boolean("Gallery Plus", default=False)
    ebay_sandbox_category_version = fields.Char("Sandbox Category Version")
    ebay_prod_category_version = fields.Char("Production Category Version")

    export_product_prices_from_date = fields.Datetime(string='Export product prices from date')

    def export_product_prices(self):
        self.ensure_one()
        export_start_time = datetime.now()
        check_active_ebay = self.env['ebay.product.template'].sudo().search_count([("ebay_listing_status", "=", "listed")])
        if check_active_ebay > 0:
            from_date = self.export_product_prices_from_date
            pricelist_items = self.env['product.pricelist.item'].search([['write_date', '>=', from_date]])
            _logger.info("EXPORT PRODUCT PRICES for ebay: found %s price list items" % (len(pricelist_items)))
            product_ids = []
            if pricelist_items:
                product_ids = pricelist_items.get_products()
            if product_ids:
                product_ids = [prod.product_tmpl_id.id for prod in product_ids]
            ebay_aricles = self.env["ebay.product.template"].search([("ebay_product_template_id", "in", product_ids),("ebay_listing_status", "=", "listed")])
            for article in ebay_aricles:
                article.revise_product_ebay()
        self.export_product_prices_from_date = export_start_time
        return True

    @api.model
    def _cron_check_price_list_item(self):
        backends = self.env['ebay.backend'].search([])
        for backend in backends:
            backend.export_product_prices()
        return True

    _sql_constraints = [('active_company_id_unique', 'unique (active,company_id)',
                         'You can activate only one configuration at the same time!')]

    def button_sync_categories(self, context=None):
        self.env['ebay.category']._cron_sync(backend_id=self)

    @api.model
    def button_sync_product_status(self, context=None):
        self.env['product.template'].sync_product_status()

    def sync_policies(self, context=None):
        self.env['ebay.policy'].sync_policies(backend_id=self)

    def synchronize_metadata(self, context=None):
        response = self.env['ebay.product.template'].ebay_execute(
            'GeteBayDetails',
            {'DetailName': ['CountryDetails', 'SiteDetails', 'CurrencyDetails']}, backend_id=self
        )
        for country in self.env['res.country'].search([('ebay_available', '=', True)]):
            country.ebay_available = False
        for country in response.dict()['CountryDetails']:
            record = self.env['res.country'].search([('code', '=', country['Country'])])
            if record:
                record.ebay_available = True
        for currency in self.env['res.currency'].search([('ebay_available', '=', True)]):
            currency.ebay_available = False
        for currency in response.dict()['CurrencyDetails']:
            record = self.env['res.currency'].with_context(active_test=False).search(
                [('name', '=', currency['Currency'])])
            if record:
                record.ebay_available = True
        for site in response.dict()['SiteDetails']:
            record = self.env['ebay.site'].search([('ebay_id', '=', site['SiteID'])])
            if not record:
                record = self.env['ebay.site'].create({
                    'name': site['Site'],
                    'ebay_id': site['SiteID']
                })
            else:
                record.name = site['Site']

    @api.model
    def get_values(self):
        res = {}
        res.update(
            ebay_dev_id=getattr(self,'ebay_dev_id', ''),
            ebay_sandbox_token=getattr(self,'ebay_sandbox_token', ''),
            ebay_sandbox_app_id=getattr(self,'ebay_sandbox_app_id', ''),
            ebay_sandbox_cert_id=getattr(self,'ebay_sandbox_cert_id', ''),
            ebay_prod_token=getattr(self,'ebay_prod_token', ''),
            ebay_prod_app_id=getattr(self,'ebay_prod_app_id', ''),
            ebay_prod_cert_id=getattr(self,'ebay_prod_cert_id', ''),
            ebay_domain=getattr(self,'ebay_domain', ''),
            ebay_currency=int(getattr(self,'ebay_currency', self.env.ref('base.USD'))),
            ebay_country=int(getattr(self, 'ebay_country', self.env.ref('base.us'))),
            ebay_site=int(getattr(self, 'ebay_site', self.env['ebay.site'].search([])[0])),
            ebay_zip_code=getattr(self,'ebay_zip_code'),
            ebay_location=getattr(self, 'ebay_location'),
            ebay_out_of_stock=getattr(self, 'ebay_out_of_stock', False),
            ebay_sales_team=int(getattr(self, 'ebay_sales_team', self.env['crm.team'].search([('team_type', '=', 'ebay')], limit=1))),
            ebay_gallery_plus=getattr(self, 'ebay_gallery_plus'),
            ebay_sandbox_category_version=getattr(self, 'ebay_sandbox_category_version',''),
            ebay_prod_category_version=getattr(self, 'ebay_prod_category_version',''),
        )
        return res

    def sync_ebay_details(self):
        response = self.env['ebay.product.template'].ebay_execute(
            'GeteBayDetails',
            {'DetailName': ['CountryDetails', 'SiteDetails', 'CurrencyDetails']}, backend_id=self
        )
        for country in self.env['res.country'].search([('ebay_available', '=', True)]):
            country.ebay_available = False
        for country in response.dict()['CountryDetails']:
            record = self.env['res.country'].search([('code', '=', country['Country'])])
            if record:
                record.ebay_available = True
        for currency in self.env['res.currency'].search([('ebay_available', '=', True)]):
            currency.ebay_available = False
        for currency in response.dict()['CurrencyDetails']:
            record = self.env['res.currency'].with_context(active_test=False).search(
                [('name', '=', currency['Currency'])])
            if record:
                record.ebay_available = True
        for site in response.dict()['SiteDetails']:
            record = self.env['ebay.site'].search([('ebay_id', '=', site['SiteID'])])
            if not record:
                record = self.env['ebay.site'].create({
                    'name': site['Site'],
                    'ebay_id': site['SiteID']
                })
            else:
                record.name = site['Site']