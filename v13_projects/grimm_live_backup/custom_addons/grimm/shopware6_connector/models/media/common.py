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
class MediaFolder(models.Model):
    _name = 'media.folder'

    shopware6_bind_ids = fields.One2many(
        comodel_name='shopware6.media.folder',
        inverse_name='openerp_id',
        string="Shopware6 Bindings",
    )
    is_shopware_exported = fields.Boolean(string='Is Exported ?', compute='_get_is_shopware_exported')

    name = fields.Char(string='Name', required=True)
    parent_id = fields.Many2one(
        comodel_name='media.folder',
        string='Parent ID',
        help='Parent directory',
    )
    child_ids = fields.One2many(
        comodel_name='media.folder',
        inverse_name='parent_id',
        string="Child Directory",
    )
    shopware_backend_id = fields.Many2one('shopware6.backend', string='Shopware6 backend')

    def _get_is_shopware_exported(self):
        for this in self:
            this.is_shopware_exported = False
            for bind in this.shopware6_bind_ids:
                if bind.shopware6_id:
                    this.is_shopware_exported = True
                    pass

    def export_to_shopware(self):
        self.ensure_one()
        backends = self.env['shopware6.backend'].search([])
        for backend in backends:
            img_binding = backend.create_bindings_for_model(self, 'shopware6_bind_ids')
        return True

class Shopware6MediaFolder(models.Model):
    _name = 'shopware6.media.folder'
    _inherit = 'shopware6.binding'
    _inherits = {'media.folder': 'openerp_id'}
    _description = 'Shopware6 Media Folder'

    openerp_id = fields.Many2one(comodel_name='media.folder',
                              string='Media Folder',
                              required=True,
                              ondelete='cascade')
    shopware6_parent_id = fields.Many2one(
        comodel_name='shopware6.media.folder',
        string='Shopware6 Parent Folder',
        ondelete='cascade',
    )
    shopware6_child_ids = fields.One2many(
        comodel_name='shopware6.media.folder',
        inverse_name='shopware6_parent_id',
        string='Shopware6 Child directory',
    )

    @job(default_channel='root.shopware6')
    @api.model
    def import_batch(self, backend, filters=None):
        """ Prepare the import of media from Shopware6 """
        if filters is None:
            filters = {}
        with backend.work_on(self._name) as work:
            importer = work.component(usage='batch.importer')
            return importer.run(filters=filters)

    @job(default_channel='root.shopware6')
    @related_action(action='related_action_unwrap_binding')
    def export_record(self, fields=None):
        """ Export Media record to Shopware 6"""
        return super(Shopware6MediaFolder, self).export_record(fields)

    @job(default_channel='root.shopware6')
    @related_action(action='related_action_shopware6_link')
    @api.model
    def import_record(self, backend, shopware6_id, force=False):
        """ Import a Shopware6 media record """
        return super(Shopware6MediaFolder, self).import_record(backend, shopware6_id, force)

class MediaFolderAdapter(Component):
    _name = 'shopware6.media.folder.adapter'
    _inherit = 'shopware6.adapter'
    _apply_on = 'shopware6.media.folder'

    _shopware_uri = 'api/v3/media-folder/'

    def search(self, filters=None):
        """ Search records according to some criterias
        and returns a list of ids

        :rtype: list
        """
        if not filters:
            filters = ''

        result = self._call('GET','%s?%s' % (self._shopware_uri,filters),{})
        return result.get('data', result)

    def read(self, id, attributes=""):
        """ Returns the information of a record

        :rtype: dict
        """
        result =self._call('GET', '%s%s%s' % (self._shopware_uri, id, attributes), [{}])
        return result.get('data', result)


class MediaFolderListener(Component):
    _name = 'media.folder.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['media.folder']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        for shopware_bind in record.shopware6_bind_ids:
            shopware_bind.with_delay().export_record(fields=fields)

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_unlink(self, record):
        for binding in record.shopware6_bind_ids:
            target_shopware_id = getattr(binding, 'shopware6_id')
            if target_shopware_id:
                binding.with_delay().export_delete_record(binding.backend_id, target_shopware_id)


class ShopwareBindingMediaFolderListener(Component):
    _name = 'shopware6.binding.media.folder.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['shopware6.media.folder']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        record.with_delay().export_record()