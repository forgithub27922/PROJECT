# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo.addons.connector.exception import MappingError
import logging
_logger = logging.getLogger(__name__)


class ProductCategoryBatchImporterShopware6(Component):
    """ Import the Shopware Product Categories.

    For every product category in the list, a delayed job is created.
    A priority is set on the jobs according to their level to rise the
    chance to have the top level categories imported first.
    """
    _name = 'shopware6.product.category.batch.importer'
    _inherit = 'shopware6.delayed.batch.importer'
    _apply_on = ['shopware6.product.category']

    def _import_record(self, shopware6_id, job_options=None, **kwargs):
        """ Delay a job for the import """
        return super(ProductCategoryBatchImporterShopware6, self)._import_record(
            shopware6_id, job_options=job_options)

    def run(self, filters=None):
        """ Run the synchronization """
        if filters is None:
            filters = []
        updated_ids = self.backend_adapter.search(filters)
        for record_id in updated_ids:
            self._import_record(record_id.get('id'))


class ProductCategoryImporterShopware6(Component):
    _name = 'shopware6.product.category.importer'
    _inherit = 'shopware6.importer'
    _apply_on = ['shopware6.product.category']


    def _import_dependencies(self):
        """ Import the dependencies for the record"""
        record = self.shopware_record.get("attributes", {})
        # import parent category
        # the root category has a null parent_id
        if record.get('parentId'):
            parent_id = record['parentId']
            if self.binder.to_internal(parent_id) is None:
                importer = self.component(usage='record.importer',model_name='shopware6.product.category')
                importer.run(parent_id)

    def _create(self, data):
        binding = super(ProductCategoryImporterShopware6, self)._create(data)
        #self.backend_record.add_checkpoint(binding)
        return binding

class ProductCategoryImportMapperShopware6(Component):
    _name = 'shopware6.product.category.import.mapper'
    _inherit = 'shopware6.import.mapper'
    _apply_on = 'shopware6.product.category'

    @mapping
    def name(self, record):
        record = record.get("attributes", {})
        if record:
            if not record.get('parentId'):  # top level category in Shopware is named "Root", better take the backend name
                return {'name': record.get('name') if record.get('name',False) else self.backend_record.name} # Here we set original name from the Shopware instead of backend name.
            else:
                return {'name': record.get('name')}

    @mapping
    def shopware6_id(self, record):
        return {'shopware6_id': record['id']}

    @mapping
    def set_meta_info(self, record):
        meta_info = {}
        record = record.get("attributes", {})
        meta_info["shopware6_meta_title"] = record.get("metaTitle")
        meta_info["shopware6_meta_description"] = record.get("metaDescription")
        meta_info["shopware6_meta_keywords"] = record.get("keywords")

        return meta_info

    @mapping
    def map_info(self, record):
        meta_info = {}
        record = record.get("attributes", {})
        meta_info["shopware6_active"] = record.get("active")
        meta_info["shopware6_category_type"] = record.get("type")
        meta_info["shopware6_category_assignment_type"] = record.get("productAssignmentType")
        meta_info["shopware6_description"] = record.get("description")

        return meta_info


    @mapping
    def parent_id(self, record):
        record = record.get("attributes", {})
        if not record.get('parentId'):
            return
        binder = self.binder_for('shopware6.product.category')
        category_id = binder.to_internal(record.get('parentId'), unwrap=True)
        sw_cat_id = False
        for shopware_bind in category_id.shopware6_bind_ids:
            sw_cat_id = shopware_bind.id
        print("During category import parent id ==> %s and shopware6_parent_id is ===> %s"%(category_id,sw_cat_id))

        if category_id is None:
            raise MappingError("The product category with "
                               "shopware id %s is not imported." %
                               record.get('parentId'))
        return {'parent_id': category_id.id, 'shopware6_parent_id': sw_cat_id}
