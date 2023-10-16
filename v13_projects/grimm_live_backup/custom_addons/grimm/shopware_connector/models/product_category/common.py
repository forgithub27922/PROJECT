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

class ShopwareProductCategory(models.Model):
    _name = 'shopware.product.category'
    _inherit = 'shopware.binding'
    _inherits = {'product.category': 'openerp_id'}
    _description = 'Shopware Product Category'

    openerp_id = fields.Many2one(comodel_name='product.category',
                              string='Product Category',
                              required=True,
                              ondelete='cascade')
    shopware_parent_id = fields.Many2one(
        comodel_name='shopware.product.category',
        string='Shopware Parent Category',
        ondelete='cascade',
    )
    created_at = fields.Date('Created At (on Shopware)')
    updated_at = fields.Date('Updated At (on Shopware)')
    shopware_child_ids = fields.One2many(
        comodel_name='shopware.product.category',
        inverse_name='shopware_parent_id',
        string='Shopware Child Categories',
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


class ProductCategory(models.Model):
    _inherit = 'product.category'

    shopware_bind_ids = fields.One2many(
        comodel_name='shopware.product.category',
        inverse_name='openerp_id',
        string="Shopware Bindings",
    )
    is_shopware_exported = fields.Boolean(string='Is Exported ?', compute='_get_is_shopware_exported')

    def _get_is_shopware_exported(self):
        for this in self:
            this.is_shopware_exported = False
            for bind in this.shopware_bind_ids:
                if bind.shopware_id:
                    this.is_shopware_exported = True
                    pass

    def export_to_shopware(self):
        self.ensure_one()
        backends = self.env['shopware.backend'].search([])
        for backend in backends:
            img_binding = backend.create_bindings_for_model(self, 'shopware_bind_ids')
        return True


class ProductCategoryAdapter(Component):
    _name = 'shopware.product.category.adapter'
    _inherit = 'shopware.adapter'
    _apply_on = 'shopware.product.category'

    _shopware_uri = 'categories/'
    _admin_path = '/{model}/index/'

    def search(self, filters=None):
        """ Search records according to some criterias
        and returns a list of ids

        :rtype: list
        """
        if filters:
            query_string = ""
            index = 0
            for filt in filters:
                query_string += "filter[%s][property]=%s&filter[%s][expression]=%s&filter[%s][value]=%s&"%(index,filt.get("property"),index,filt.get("expression","="),index,filt.get("value"))
                index += 1
            self._shopware_uri = "categories?%s"%query_string
        return self._call('get','%s' % self._shopware_uri,{})

    def read(self, id, attributes=None):
        """ Returns the information of a record

        :rtype: dict
        """
        return self._call('get', '%s%s' % (self._shopware_uri, id), [{}])

    def write(self, id, data):
        """ Update category on the Shopware system """
        return self._call('put', '%s%s' % (self._shopware_uri, id), data)

    def create(self, data):
        return self._call('post', self._shopware_uri, data)

    def move(self, categ_id, parent_id, after_categ_id=None):
        return self._call('%s.move' % self._shopware_model,
                          [categ_id, parent_id, after_categ_id])

    def get_assigned_product(self, categ_id):
        return self._call('%s.assignedProducts' % self._shopware_model,
                          [categ_id])

    def assign_product(self, categ_id, product_id, position=0):
        return self._call('%s.assignProduct' % self._shopware_model,
                          [categ_id, product_id, position, 'id'])

    def update_product(self, categ_id, product_id, position=0):
        return self._call('%s.updateProduct' % self._shopware_model,
                          [categ_id, product_id, position, 'id'])

    def remove_product(self, categ_id, product_id):
        return self._call('%s.removeProduct' % self._shopware_model,
                          [categ_id, product_id, 'id'])


class ProductCategoryListener(Component):
    _name = 'product.category.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['product.category']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        for shopware_bind in record.shopware_bind_ids:
            run_trigger = shopware_bind.backend_id.check_allowed_fields(model_name=record._name, fields=fields)
            if run_trigger:
                shopware_bind.with_delay().export_record(fields=fields)

class ShopwareBindingProductCategoryListener(Component):
    _name = 'shopware.binding.product.category.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['shopware.product.category']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        record.with_delay().export_record()