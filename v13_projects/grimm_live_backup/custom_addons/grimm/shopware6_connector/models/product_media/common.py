# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from slugify import slugify
import uuid
import pytz
from odoo import models, fields, api
from odoo.addons.connector.exception import IDMissingInBackend
from odoo.addons.component_event import skip_if
from odoo.addons.component.core import Component
from ...components.backend_adapter import SHOPWARE_DATETIME_FORMAT
import base64
import os
from odoo.addons.queue_job.job import job, related_action

_logger = logging.getLogger(__name__)
class ProductMedia(models.Model):
    _name = 'product.media'

    shopware6_bind_ids = fields.One2many(
        comodel_name='shopware6.product.media',
        inverse_name='openerp_id',
        string="Shopware6 Bindings",
    )
    shopware6_media_file_bind_ids = fields.One2many(
        comodel_name='shopware6.product.media.file',
        inverse_name='openerp_id',
        string="Shopware6 Media File",
    )
    is_shopware_exported = fields.Boolean(string='Is Exported ?', compute='_get_is_shopware_exported')

    name = fields.Char(string='Name', required=True)
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product Id',
        help='Product ID',
        ondelete='cascade'
    )
    product_tmpl_id = fields.Many2one(
        comodel_name='product.template',
        string='Product Template Id',
        help='Product ID',
        ondelete='cascade'
    )
    file_name = fields.Char('File Name')
    set_as_cover = fields.Boolean('Set as Cover ?')
    file_select = fields.Selection(string='Upload Option', selection=[('upload', 'Upload File'),('base', 'Base')], required=True,
                                   default='upload')
    file_url = fields.Char('File URL')
    position = fields.Integer(string='Position', store=True)
    image = fields.Binary("Shopware6 Image", attachment=True, help="Shopware6 Image.", )
    related_image = fields.Binary("Shopware6 Image", related="product_id.image_1920", help="Shopware6 Image." )

    def _get_is_shopware_exported(self):
        for this in self:
            this.is_shopware_exported = False
            for bind in this.shopware6_bind_ids:
                if bind.shopware6_id:
                    this.is_shopware_exported = True
                    pass

    def export_to_shopware_media(self):
        self.ensure_one()
        backends = self.env['shopware6.backend'].search([])
        for backend in backends:
            img_binding = backend.create_bindings_for_model(self, 'shopware6_media_file_bind_ids')
            img_binding.export_record()
        return True

class Shopware6ProductMediaFile(models.Model):
    _name = 'shopware6.product.media.file'
    _inherit = 'shopware6.binding'
    _inherits = {'product.media': 'openerp_id'}
    _description = 'Shopware6 Product Media File'

    openerp_id = fields.Many2one(comodel_name='product.media',
                              string='Product Media',
                              required=True, ondelete='cascade')

    @job(default_channel='root.shopware6')
    @related_action(action='related_action_shopware6_link')
    @api.model
    def import_record(self, backend, shopware6_id, force=False):
        """ Import a Shopware6 product Media record """
        return super(Shopware6ProductMedia, self).import_record(backend, shopware6_id, force)

class Shopware6ProductMedia(models.Model):
    _name = 'shopware6.product.media'
    _inherit = 'shopware6.binding'
    _inherits = {'product.media': 'openerp_id'}
    _description = 'Shopware6 Product Media'

    openerp_id = fields.Many2one(comodel_name='product.media',
                              string='Product Media',
                              required=True,
                              ondelete='cascade')

    @job(default_channel='root.shopware6')
    @related_action(action='related_action_unwrap_binding')
    def export_record(self, fields=None):
        """ Export Product Media record to Shopware 6"""
        return super(Shopware6ProductMedia, self).export_record(fields)

    @job(default_channel='root.shopware6')
    @related_action(action='related_action_shopware6_link')
    @api.model
    def import_record(self, backend, shopware6_id, force=False):
        """ Import a Shopware6 product Media record """
        return super(Shopware6ProductMedia, self).import_record(backend, shopware6_id, force)

class ProductMediaAdapter(Component):
    _name = 'shopware6.product.media.adapter'
    _inherit = 'shopware6.adapter'
    _apply_on = 'shopware6.product.media'

    _shopware_uri = 'api/v3/product-media/'

    def set_as_cover(self, product_id, data):
        return self._call('PATCH', '%s%s' % ('api/v3/product/', product_id), data)

class ProductMediaFileAdapter(Component):
    _name = 'shopware6.product.media.file.adapter'
    _inherit = 'shopware6.adapter'
    _apply_on = 'shopware6.product.media.file'

    _shopware_uri = 'api/v3/media/'

    def isBase64(self, s):
        try:
            return base64.b64encode(base64.b64decode(s)) == s
        except Exception:
            return False

    def set_image(self, binding):
        """ Update records on the external system """
        # XXX actually only ol_catalog_product.update works
        # the PHP connector maybe breaks the catalog_product.update
        file_name_extension = [binding.openerp_id.product_id.default_code, ".jpg"]
        #if product_media.file_name:
        #    file_name_extension = os.path.splitext(product_media.file_name)
        #shopware_uri = "api/v2/_action/media/%s/upload?extension=%s&fileName=%s"%(id,str(file_name_extension[1].replace(".","")),file_name_extension[0])
        file_name = ""

        if binding.openerp_id.product_id:
            image_data = base64.decodestring(binding.openerp_id.image if binding.openerp_id.file_select == 'upload' else binding.openerp_id.related_image)
            file_name = slugify(str(binding.openerp_id.product_id.name)+str("-")+str(uuid.uuid4().hex[:5]))
        if binding.openerp_id.product_tmpl_id:
            if binding.openerp_id.file_select == 'base':
                image_data = binding.openerp_id.product_tmpl_id.image_1920
            else:
                image_data = binding.openerp_id.image
            file_name = slugify(str(binding.openerp_id.product_tmpl_id.name) + str("-") + str(uuid.uuid4().hex[:5]))

        if self.isBase64(image_data):
            image_data = base64.decodebytes(image_data)
        shopware_uri = "api/v2/_action/media/%s/upload?extension=%s&fileName=%s" % (binding.shopware6_id, str(file_name_extension[1].replace(".", "")), file_name)
        return self._call('POST', shopware_uri, image_data)


class ProductMediaListener(Component):
    _name = 'product.media.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['product.media']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        for shopware_bind in record.shopware6_bind_ids:
            shopware_bind.with_delay().export_record(fields=fields)
        for shopware_bind in record.shopware6_media_file_bind_ids:
            shopware_bind.export_record(fields=fields)



    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_unlink(self, record):
        for binding in record.shopware6_bind_ids:
            target_shopware_id = getattr(binding, 'shopware6_id')
            if target_shopware_id:
                binding.with_delay().export_delete_record(binding.backend_id, target_shopware_id)
        for binding in record.shopware6_media_file_bind_ids:
            target_shopware_id = getattr(binding, 'shopware6_id')
            if target_shopware_id:
                binding.with_delay().export_delete_record(binding.backend_id, target_shopware_id)


class Shopware6BindingProductMediaListener(Component):
    _name = 'shopware6.binding.product.media.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['shopware6.product.media']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        record.with_delay().export_record()

class Shopware6BindingProductMediaFileListener(Component):
    _name = 'shopware6.binding.product.media.file.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['shopware6.product.media.file']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        record.export_record()
