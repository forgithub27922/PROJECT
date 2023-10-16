# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import io
import re

from datetime import datetime, timedelta
from ebaysdk.exception import ConnectionError
from odoo.addons.sale_ebay.tools.ebaysdk import Trading
from xml.sax.saxutils import escape

from odoo import models, fields, api, _
from odoo.exceptions import UserError, RedirectWarning
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools import pycompat

import logging

_logger = logging.getLogger(__name__)

# eBay api limits ItemRevise calls to 150 per day
MAX_REVISE_CALLS = 150


class ProductTemplate(models.Model):
    _inherit = "product.template"

    #calculated_ebay_price = fields.Monetary(string='Ebay Price', help='Calculated Price for Ebay', related='product_variant_ids.calculated_ebay_price')
    ebay_listing_status = fields.Selection([('listed', 'Listed'), ('unlisted', 'Unlisted')], string='eBay Status', default='unlisted',readonly=True, copy=False)

    def tracking_ebay_price(self):
        self.ensure_one()
        if len(self.product_variant_ids) == 1:
            return self.product_variant_ids[0].tracking_ebay_price()
        raise Warning(
            'Product Template hat multiple Product Variants. Please tracking the price calculation on the Product Variant')

    @api.model
    def get_ebay_api(self, domain, backend_id=False):
        ebay_api = self.env["ebay.backend"].search([('company_id', '=', self.env.user.company_id.id)], limit=1)
        if backend_id:
            ebay_api=backend_id
        if not ebay_api:
            raise UserError("Please configure Ebay backend for "+str(self.user.company_id.name))
        dev_id = ebay_api.ebay_dev_id
        site_id = ebay_api.ebay_site
        site = self.env['ebay.site'].browse(int(site_id))
        if domain == 'sand':
            app_id = ebay_api.ebay_sandbox_app_id
            cert_id = ebay_api.ebay_sandbox_cert_id
            token = ebay_api.ebay_sandbox_token
            domain = 'api.sandbox.ebay.com'
        else:
            app_id = ebay_api.ebay_prod_app_id
            cert_id = ebay_api.ebay_prod_cert_id
            token = ebay_api.ebay_prod_token
            domain = 'api.ebay.com'

        if not app_id or not cert_id or not token:
            action = self.env.ref('sale.action_sale_config_settings')
            raise RedirectWarning(_('One parameter is missing.'),
                                  action.id, _('Configure The eBay Integrator Now'))

        return Trading(domain=domain,
                       config_file=None,
                       appid=app_id,
                       devid=dev_id,
                       certid=cert_id,
                       token=token,
                       siteid=site.ebay_id)

    @api.model
    def ebay_execute(self, verb, data=None, list_nodes=[], verb_attrs=None, files=None, backend_id=False):
        ebay_backend_id = self.env["ebay.backend"].search([('company_id', '=', self.env.user.company_id.id)],
                                                              limit=1)
        if backend_id:
            ebay_backend_id = backend_id
        if not ebay_backend_id:
            raise UserError("Please configure Ebay backend for "+str(self.user.company_id.name))
        domain = ebay_backend_id.get_values()["ebay_domain"]
        ebay_api = self.get_ebay_api(domain, backend_id=backend_id)
        try:
            return ebay_api.execute(verb, data, list_nodes, verb_attrs, files)
        except ConnectionError as e:
            errors = e.response.dict()['Errors']
            if not isinstance(errors, list):
                errors = [errors]
            error_message = ''
            for error in errors:
                if error['SeverityCode'] == 'Error':
                    error_message += error['LongMessage'] + '(' + error['ErrorCode'] + ')'
            if error['ErrorCode'] == '21916884':
                error_message += _('Or the condition is not compatible with the category.')
            if error['ErrorCode'] == '10007' or error['ErrorCode'] == '21916803':
                error_message = _('eBay is unreachable. Please try again later.')
            if error['ErrorCode'] == '21916635':
                error_message = _(
                    'Impossible to revise a listing into a multi-variations listing.\n Create a new listing.')
            if error['ErrorCode'] == '942':
                error_message += _(" If you want to set quantity to 0, the Out Of Stock option should be enabled"
                                   " and the listing duration should set to Good 'Til Canceled")
            if error['ErrorCode'] == '21916626':
                error_message = _(" You need to have at least 2 variations selected for a multi-variations listing.\n"
                                  " Or if you try to delete a variation, you cannot do it by unselecting it."
                                  " Setting the quantity to 0 is the safest method to make a variation unavailable.")
            raise UserError(_("Error Encountered.\n'%s'") % (error_message,))


class ProductProduct(models.Model):
    _inherit = "product.product"

    calculated_ebay_price = fields.Monetary(string='Ebay Price', help='Calculated Sale Price (for Ebay)',
                                            compute='_compute_ebay_price')

    def _compute_ebay_price(self):
        ebay_api = self.env['ebay.backend'].search([('company_id', '=', self.env.user.company_id.id)])
        pricelist_id = ebay_api.pricelist_id if ebay_api else self.env.user.company_id.pricelist_id
        currency_id = ebay_api.ebay_currency if ebay_api else self.env.user.company_id.currency_id
        for record in self:
            if pricelist_id:
                product = record.with_context(
                    quantity=1,
                    pricelist=pricelist_id.id,
                    currency_id=currency_id,
                )
                try:
                    record.calculated_ebay_price = product.price
                except:
                    record.calculated_ebay_price = product.price
            else:
                record.calculated_ebay_price = record.list_price

    def tracking_ebay_price(self):
        self.ensure_one()
        tracking_id = self.env["shop.price.tracking"].create(
            {"price_track": "<h3 style='color:red;'>Price Tracking</h3>"})
        ebay_api = self.env['ebay.backend'].search([('company_id', '=', self.env.user.company_id.id)])
        pricelist_id = ebay_api.pricelist_id if ebay_api else self.env.user.company_id.pricelist_id
        trackings = []
        if pricelist_id:
            res = pricelist_id.with_context(track=True)._compute_price_rule(
                list(pycompat.izip(self, [1] * len(self), [False] * len(self))), flush=True)
            trackings = res[self.id][3]
            track_info = self._get_tracking_message(trackings)
            tracking_id.price_track = track_info

        return {
            'name': _('Price Tracking Information'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'shop.price.tracking',
            'res_id': tracking_id.id,
            'type': 'ir.actions.act_window',
            'target': 'new',
        }