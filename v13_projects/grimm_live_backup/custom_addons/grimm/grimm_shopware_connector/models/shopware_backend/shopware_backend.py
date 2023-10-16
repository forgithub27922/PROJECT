# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2016 Openfellas (http://openfellas.com) All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly advised to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

# from ..unit.product_import import prepare_nonconfig_product_prices_batch_import
import logging
from datetime import datetime, timedelta

from odoo import models, fields, api
from odoo.exceptions import Warning

_logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-

from odoo import models, api

class ShopwareBackend(models.Model):
    _inherit = 'shopware.backend'

    export_product_prices_from_date = fields.Datetime(string='Export product prices from date')

    def export_product_prices(self):
        self.ensure_one()
        export_start_time = datetime.now()
        from_date = self.export_product_prices_from_date
        pricelist_items = self.env['product.pricelist.item'].search([['write_date', '>=', from_date]])
        _logger.info("EXPORT PRODUCT PRICES: found %s price list items" % (len(pricelist_items)))
        if pricelist_items:
            pricelist_items.check_shopware_products_prices(pricelist=self.default_company_id.pricelist_id)

        # Grimm START
        product_ids = []
        purchase_pricelist_items = self.env['partner.pricelist.item'].search([['write_date', '>=', from_date]])
        sale_pricelist_items = self.env['partner.sale.pricelist.item'].search([['write_date', '>=', from_date]])
        partner_ids = [part.partner_id.id for part in purchase_pricelist_items]
        partner_ids.extend([part.partner_id.id for part in sale_pricelist_items])
        for partner in partner_ids:
            product_product = self.env["product.product"].search(['|', ('seller_ids.name', '=', partner), ('seller_ids.name.child_ids', '=', partner)])
            product_ids.extend([product.product_tmpl_id for product in product_product])
        counter = 0
        length = len(product_ids)
        for p_id in product_ids:
            is_shopware = self.env['shopware.product.template'].search([('openerp_id', '=', p_id.id)],limit=1, )
            if is_shopware:
                try:
                    is_available = self.env['shopware.product.update.queue'].search([('product_id', '=', p_id.product_variant_id.id)],limit=1, )
                    if is_available:
                        is_available.is_done = False
                    else:
                        self.env['shopware.product.update.queue'].create({'product_id': p_id.product_variant_id.id, 'is_done':False})
                        _logger.info("[%s/%s] added Shopware(Partenics) Product %s into the queue for price update" % (counter, length, p_id))
                except Exception as e:
                    _logger.warn(str(e))
                    _logger.info("[%s/%s] can't add Product %s into the shopware(Partenics) product price queue" % (counter, length, p_id))
        # Grimm END
        self.export_product_prices_from_date = export_start_time
        return True

    @api.model
    def _cron_check_price_list_item(self):
        print("\n\n\n_cron_check_price_list_item is called from shopware backend")
        backends = self.env['shopware.backend'].search([])
        for backend in backends:
            backend.export_product_prices()
        return True