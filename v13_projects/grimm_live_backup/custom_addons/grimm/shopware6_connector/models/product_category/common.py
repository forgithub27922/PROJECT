# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import pytz
from odoo import models, fields, api
from odoo.addons.connector.exception import IDMissingInBackend
from odoo.addons.component_event import skip_if
from odoo.addons.component.core import Component
from ...components.backend_adapter import SHOPWARE_DATETIME_FORMAT
from odoo.addons.queue_job.job import job, related_action

_logger = logging.getLogger(__name__)

class Shopware6ProductCategory(models.Model):
    _name = 'shopware6.product.category'
    _inherit = 'shopware6.binding'
    _inherits = {'product.category': 'openerp_id'}
    _description = 'Shopware6 Product Category'

    openerp_id = fields.Many2one(comodel_name='product.category',
                              string='Product Category',
                              required=True,
                              ondelete='cascade')
    shopware6_parent_id = fields.Many2one(
        comodel_name='shopware6.product.category',
        string='Shopware Parent Category',
        ondelete='cascade',
    )
    shopware_child_ids = fields.One2many(
        comodel_name='shopware6.product.category',
        inverse_name='shopware6_parent_id',
        string='Shopware6 Child Categories',
    )

    @job(default_channel='root.shopware')
    @api.model
    def import_batch(self, backend, filters=None):
        """ Prepare the import of product category from Shopware """
        if filters is None:
            filters = {}
        with backend.work_on(self._name) as work:
            importer = work.component(usage='batch.importer')
            return importer.run(filters=filters)

    @job(default_channel='root.shopware6')
    @related_action(action='related_action_unwrap_binding')
    def export_record(self, fields=None):
        """ Export product category record to Shopware 6"""
        return super(Shopware6ProductCategory, self).export_record(fields)

    @job(default_channel='root.shopware6')
    @related_action(action='related_action_shopware6_link')
    @api.model
    def import_record(self, backend, shopware6_id, force=False):
        """ Import a Shopware6 product category record """
        return super(Shopware6ProductCategory, self).import_record(backend, shopware6_id, force)


class ProductCategory(models.Model):
    _inherit = 'product.category'

    shopware6_bind_ids = fields.One2many(
        comodel_name='shopware6.product.category',
        inverse_name='openerp_id',
        string="Shopware Bindings",
    )
    is_shopware6_exported = fields.Boolean(string='Is Exported ?', compute='_get_is_shopware6_exported', store=True)

    shopware6_active = fields.Boolean(string='Active on Shopware', default=True)
    shopware6_category_type = fields.Selection(
        selection=[('page', 'Category'),
                   ('folder', 'Structuring Element'),
                   ('link', 'Customisable Link')],
        string='Shopware Category Type',
        default='page',
        required=True,
        help="It will set category type on shopware.",
    )
    shopware6_category_assignment_type = fields.Selection(
        selection=[('product', 'Manual Selection'),
                   ('product_stream', 'Dynamic product group')],
        string='Assignment Type',
        default='product',
        required=True,
        help="It will set category assignment type on shopware.",
    )
    shopware6_description = fields.Html('Description')
    shopware6_meta_title = fields.Html('Meta Title')
    shopware6_meta_description = fields.Html('Meta Description')
    shopware6_meta_keywords = fields.Html('Meta Keywords')

    @api.depends('shopware6_bind_ids', 'name', 'shopware6_description', 'shopware6_active')
    def _get_is_shopware6_exported(self):
        for this in self:
            this.is_shopware6_exported = False
            for bind in this.shopware6_bind_ids:
                if bind.shopware6_id:
                    this.is_shopware6_exported = True


    def export_to_shopware6(self):
        self.ensure_one()
        backends = self.env['shopware6.backend'].search([])
        for backend in backends:
            img_binding = backend.create_bindings_for_model(self, 'shopware6_bind_ids')
        return True


class ProductCategoryAdapter6(Component):
    _name = 'shopware6.product.category.adapter'
    _inherit = 'shopware6.adapter'
    _apply_on = 'shopware6.product.category'

    _shopware_uri = 'api/v3/category/'

    def search(self, filters=None):
        """ Search records according to some criterias
        and returns a list of ids

        :rtype: list
        """
        if not filters:
            filters = ''
        result = self._call('GET','%s?%s' % (self._shopware_uri,filters),{})
        return result.get('data', result)

    def read(self, id, attributes=None):
        """ Returns the information of a record

        :rtype: dict
        """
        result = self._call('GET', '%s%s' % (self._shopware_uri, id), [{}])
        return result.get('data', result)

    def write(self, id, data):
        """ Update category on the Shopware system """
        return self._call('PATCH', '%s%s' % (self._shopware_uri, id), data)

    def delete(self, id):
        return self._call('DELETE', '%s%s' % (self._shopware_uri, id), [{}])

    def create(self, data):
        return self._call('POST', self._shopware_uri, data)

class ProductCategory6Listener(Component):
    _name = 'product.category.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['product.category']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        backends = self.env['shopware6.backend'].search([])
        for shopware_bind in record.shopware6_bind_ids:
            shopware_bind.with_delay().export_record(fields=fields)

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_unlink(self, record):
        for binding in record.shopware6_bind_ids:
            target_shopware_id = getattr(binding, 'shopware6_id')
            if target_shopware_id:
                binding.with_delay(description="Delete %s category to %s"%(target_shopware_id, binding.backend_id.name)).export_delete_record(binding.backend_id, target_shopware_id)


class ShopwareBindingProductCategory6Listener(Component):
    _name = 'shopware6.binding.product.category.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['shopware6.product.category']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        record.with_delay().export_record()