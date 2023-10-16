# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo.addons.connector.exception import MappingError
import logging
_logger = logging.getLogger(__name__)


class MediaFolderBatchImporter(Component):
    """ Import the Shopware6 Product Categories.

    For every product category in the list, a delayed job is created.
    A priority is set on the jobs according to their level to rise the
    chance to have the top level categories imported first.
    """
    _name = 'shopware6.media.folder.batch.importer'
    _inherit = 'shopware6.delayed.batch.importer'
    _apply_on = ['shopware6.media.folder']

    def _import_record(self, shopware6_id, job_options=None, **kwargs):
        """ Delay a job for the import """
        return super(MediaFolderBatchImporter, self)._import_record(
            shopware6_id, job_options=job_options)

    def run(self, filters=None):
        """ Run the synchronization """
        if filters is None:
            filters = []
        updated_ids = self.backend_adapter.search(filters)
        for record_id in updated_ids:
            self._import_record(record_id.get('id'))


class MediaFolderImporter(Component):
    _name = 'shopware6.media.folder.importer'
    _inherit = 'shopware6.importer'
    _apply_on = ['shopware6.media.folder']


    def _import_dependencies(self):
        """ Import the dependencies for the record"""
        record = self.shopware_record
        # import parent category
        # the root category has a null parent_id
        attr = record.get("data", {}).get("attributes", {})
        if attr.get('parentId'):
            parent_id = attr['parentId']
            if self.binder.to_openerp(parent_id) is None:
                importer = self.component(usage='record.importer',model_name='shopware6.media.folder')
                importer.run(parent_id)


class MediaFolderImportMapper(Component):
    _name = 'shopware6.media.folder.import.mapper'
    _inherit = 'shopware6.import.mapper'
    _apply_on = 'shopware6.media.folder'

    @mapping
    def name(self, record):
        attr = record.get("attributes", {})

        if attr:
            return {'name': attr.get('name')}

    @mapping
    def shopware6_id(self, record):
        return {'shopware6_id': record['id']}

    @mapping
    def shopware6_backend_id(self, record):
        return {'shopware_backend_id': self.backend_record.id}

    @mapping
    def parent_id(self, record):
        attr = record.get("attributes", {})
        if not attr.get('parentId'):
            return {'shopware_backend_id':self.backend_record.id}
        binder = self.binder_for('shopware6.media.folder')
        folder_id = binder.to_internal(attr.get('parentId'), unwrap=True)
        sw_cat_id = False
        for shopware_bind in folder_id.shopware6_bind_ids:
            sw_cat_id = shopware_bind.id
        return {'parent_id': folder_id.id, 'shopware6_parent_id': sw_cat_id}
