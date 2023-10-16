# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo.addons.connector.exception import MappingError


class ProductCategoryBatchImporter(Component):
    """ Import the Shopware Product Categories.

    For every product category in the list, a delayed job is created.
    A priority is set on the jobs according to their level to rise the
    chance to have the top level categories imported first.
    """
    _name = 'shopware.product.category.batch.importer'
    _inherit = 'shopware.delayed.batch.importer'
    _apply_on = ['shopware.product.category']

    def _import_record(self, shopware_id, job_options=None, **kwargs):
        """ Delay a job for the import """
        return super(ProductCategoryBatchImporter, self)._import_record(
            shopware_id, job_options=job_options)

    def run(self, filters=None):
        """ Run the synchronization """
        if filters is None:
            filters = []
        updated_ids = self.backend_adapter.search(filters)

        #for updated in updated_ids:
        #    if updated['parentId'] == None:
        #        updated['parentId'] = 0
        #updated_ids = sorted(updated_ids, key=lambda k: k['parentId'])
        for record_id in updated_ids:
            self._import_record(record_id.get('id'))


class ProductCategoryImporter(Component):
    _name = 'shopware.product.category.importer'
    _inherit = 'shopware.importer'
    _apply_on = ['shopware.product.category']


    def _import_dependencies(self):
        """ Import the dependencies for the record"""
        record = self.shopware_record
        # import parent category
        # the root category has a null parent_id
        if record.get('parentId'):
            parent_id = record['parentId']
            if self.binder.to_openerp(parent_id) is None:
                importer = self.component(usage='record.importer',model_name='shopware.product.category')
                importer.run(parent_id)

    def _create(self, data):
        binding = super(ProductCategoryImporter, self)._create(data)
        #self.backend_record.add_checkpoint(binding)
        return binding

class ProductCategoryImportMapper(Component):
    _name = 'shopware.product.category.import.mapper'
    _inherit = 'shopware.import.mapper'
    _apply_on = 'shopware.product.category'

    @mapping
    def name(self, record):
        if not record.get('parentId'):  # top level category in Shopware is named "Root", better take the backend name
            return {'name': self.backend_record.name}
        else:
            return {'name': record['name']}

    @mapping
    def shopware_id(self, record):
        return {'shopware_id': record['id']}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def parent_id(self, record):
        if not record.get('parentId'):
            return
        binder = self.binder_for('shopware.product.category')
        category_id = binder.to_internal(record['parentId'], unwrap=True)
        sw_cat_id = binder.to_openerp(record['parentId'])

        if category_id is None:
            raise MappingError("The product category with "
                               "shopware id %s is not imported." %
                               record['parentId'])
        return {'parent_id': category_id.id, 'shopware_parent_id': sw_cat_id}
