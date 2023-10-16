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
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

from odoo import models, fields, api
from odoo.addons.connector_magento.models.magento_backend.common import IMPORT_DELTA_BUFFER
# from odoo.addons.magentoerpconnect.unit.import_synchronizer import import_batch
# from odoo.addons.magentoerpconnect.unit.import_synchronizer import import_record
from odoo.addons.of_base_magento_extensions_v9.constants import PRODUCTS_MAGENTO_MASTER, PRODUCTS_ODOO_MASTER
from odoo.exceptions import Warning

_logger = logging.getLogger(__name__)


class MagentoBackend(models.Model):
    _inherit = 'magento.backend'

    attrs_default_storeview_id = fields.Many2one('magento.storeview', string='Default storeview for attributes')
    order_payment_mode_mapping_ids = fields.One2many('magento.payment.mode.mapping', 'backend_id',
                                                     'Order payment mode mappings')

    import_product_prices_from_date = fields.Datetime(string='Import product prices from date')
    export_product_prices_from_date = fields.Datetime(string='Import product prices from date')
    import_grimm_relation_from_date = fields.Datetime(string='Import grimm relation from date')
    orders_project_id = fields.Many2one('account.analytic.account', string='Analytic account for orders',
                                        domain=[('account_type', '=', 'normal')])
    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist', required=True)
    default_company_id = fields.Many2one(
        comodel_name='res.company',
        string='Default company',
        help='When we import any record like Sale Orders etc will be created for this company.',
    )

    @api.model
    def select_versions(self):
        res = super(MagentoBackend, self).select_versions()
        res.append(('1.7.2', 'Grimm Magento Extensions (1.7+)'))
        return res

    def _start_products_batch_import(self, session, product_model, history_id, filters={}):
        if self.env.context.get('search_created_only', False):
            filters['search_created_only'] = True

        super(MagentoBackend, self)._start_products_batch_import(session, product_model, history_id, filters=filters)

    def import_new_products(self):
        for backend in self:
            history = self.env['products.import.history'].create({'backend_id': backend.id})
            backend.with_context(import_history_id=history.id, search_created_only=True)._import_from_date(
                'magento.product.template', 'import_configurable_products_from_date'
            )

            backend.with_context(import_history_id=history.id, skip_config_date_update=True,
                                 search_created_only=True)._import_from_date(
                'magento.product.product', 'import_products_from_date'
            )

    def import_new_grimm_relation(self):
        for backend in self:
            backend.with_context(search_created_only=True)._import_from_date(
                'magento.product.link', 'import_grimm_relation_from_date'
            )

    def import_product_product(self):
        for backend in self:
            if backend.products_sync_type == PRODUCTS_MAGENTO_MASTER:
                super(MagentoBackend, backend).import_product_product()
            else:
                backend.import_new_products()

    def import_product_prices(self):
        # self.ensure_one()
        #
        # if self.products_sync_type != PRODUCTS_ODOO_MASTER:
        #     return False
        #
        # session = ConnectorSession(self.env.cr, self.env.uid, self._context)
        #
        # import_start_time = datetime.now()
        #
        # from_date = self.import_product_prices_from_date
        # if from_date:
        #     from_date = fields.Datetime.from_string(from_date)
        # else:
        #     from_date = None
        #
        # prepare_nonconfig_product_prices_batch_import.delay(session, 'magento.product.product', self.id,
        #                                                     filters={'from_date': from_date,
        #                                                              'to_date': import_start_time})
        #
        # next_time = import_start_time - timedelta(seconds=IMPORT_DELTA_BUFFER)
        # next_time = fields.Datetime.to_string(next_time)
        # self.write({'import_product_prices_from_date': next_time})

        # return True

        raise Warning('Not implemented.')

    def _get_order_prepayment_val(self, payment_mode_id):
        self.ensure_one()
        res = False
        for mapp in self.order_payment_mode_mapping_ids:
            res = mapp.order_prepayment if payment_mode_id in mapp.payment_mode_ids.ids else not mapp.order_prepayment
        return res

    @api.model
    def _scheduler_import_product_prices(self):
        backends = self.env['magento.backend'].search([('products_sync_type', '=', PRODUCTS_ODOO_MASTER)])

        for backend in backends:
            backend.import_product_prices()

        return True

    def export_product_prices(self):
        self.ensure_one()
        export_start_time = datetime.now()
        from_date = self.export_product_prices_from_date
        pricelist_items = self.env['product.pricelist.item'].search([['write_date', '>=', from_date]])
        _logger.info("EXPORT PRODUCT PRICES: found %s price list items" % (len(pricelist_items)))
        if pricelist_items:
            pricelist_items.check_products_prices(pricelist=self.pricelist_id)

        # Update based on vendor price list START
        product_ids = []
        purchase_pricelist_items = self.env['partner.pricelist.item'].search([['write_date', '>=', from_date]])
        sale_pricelist_items = self.env['partner.sale.pricelist.item'].search([['write_date', '>=', from_date]])
        partner_ids = [part.partner_id.id for part in purchase_pricelist_items]
        partner_ids.extend([part.partner_id.id for part in sale_pricelist_items])
        for partner in partner_ids:
            product_product = self.env["product.product"].search(['|', ('seller_ids.name', '=', partner), ('seller_ids.name.child_ids', '=', partner)])
            product_ids.extend([product.id for product in product_product])
        counter = 0
        product_ids = list(set(product_ids))
        length = len(product_ids)
        for product in product_ids:
            counter += 1
            try:
                is_available = self.env['product.update.queue'].search([('product_id', '=', product)], limit=1, )
                if not is_available:
                    self.env['product.update.queue'].create({'product_id': product})
                    _logger.info("[%s/%s] added Product %s into the queue from vendor price list" % (counter, length, product))
            except Exception as e:
                _logger.warn(str(e))
                _logger.info("[%s/%s] can't add Product %s into the queue from vendor price list" % (counter, length, product))
        # Update based on vendor price list END

        self.export_product_prices_from_date = export_start_time
        return True

    @api.model
    def _cron_check_price_list_item(self):
        backends = self.env['magento.backend'].search([('products_sync_type', '=', PRODUCTS_ODOO_MASTER)])
        for backend in backends:
            backend.export_product_prices()

        return True

    @api.model
    def _auto_check_expired_price(self):
        current_datetime = str(datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT))
        query = "select id from product_product where active='t' and special_purchase_price is not null and special_purchase_price_to is not null and special_purchase_price_from is not null and special_purchase_price_to < '%s'" % (current_datetime)
        self._cr.execute(query)
        product_ids =[i[0] for i in self._cr.fetchall()]
        length = len(product_ids)
        counter = 0
        for product_id in product_ids:
            counter += 1
            try:
                self.env['product.update.queue'].create({'product_id': product_id})
                _logger.info("[%s/%s] added Product %s into the queue" % (counter, length, product_id))
            except Exception as e:
                _logger.warn(str(e))
                _logger.info("[%s/%s] can't add Product %s into the queue" % (counter, length, product_id))
        counter = 0
        for product_id in product_ids:
            counter += 1
            try:
                self.env['shopware.product.update.queue'].create({'product_id': product_id})
                _logger.info(
                    "[%s/%s] added Shopware Product %s into the queue for price update" % (counter, length, product_id))
            except Exception as e:
                _logger.warn(str(e))
                _logger.info("[%s/%s] can't add Product %s into the shopware product price queue" % (
                counter, length, product_id))
        for prod_id in product_ids:
            query = "update product_product set special_purchase_price_from=null where id = %s" % prod_id
            self._cr.execute(query)

class PaymentModeMapping(models.Model):
    _name = 'magento.payment.mode.mapping'
    _description = 'Payment mode mapping'

    backend_id = fields.Many2one('magento.backend', string='Magento backend')
    payment_mode_ids = fields.Many2many('account.payment.mode', 'payment_mode_mapping_payment_rel', 'payment_mapp_id',
                                        'payment_mode_id', 'Payment modes', required=True)

    order_prepayment = fields.Boolean('Order prepayment?')

    _sql_constraints = [('payment_mode_map_backend_unique', 'unique (backend_id)',
                         'You can specify one mapping per Magento backend!')]
