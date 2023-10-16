# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import xmlrpc.client
from slugify import slugify
from collections import defaultdict
import base64
import requests

from odoo import models, fields, api
from odoo.addons.connector.exception import IDMissingInBackend
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.queue_job.job import job, related_action
from odoo.exceptions import UserError, ValidationError
import mimetypes
from odoo.tools.mimetypes import guess_mimetype
import uuid
import pafy

_logger = logging.getLogger(__name__)


class MediaManager(models.Model):
    _name = 'media.manager'

    name = fields.Char('Title', required=1)
    type = fields.Selection(string='Type', selection=[('url', 'URL'), ('binary', 'File')],default='binary', required=True)
    url = fields.Char('URL')
    media_url = fields.Char('Media URL')
    active = fields.Boolean('Active', default=True)
    send_email = fields.Boolean('Send Email', default=False, help="If its set true odoo will send an safety email to customer after order confirmation of those product.")
    document_type = fields.Many2one("product.document.type", string="Document Type")
    data = fields.Binary("Attachment", attachment=True, help="Shopware6 attachments like images, pdf etc. ")
    filename = fields.Char('Filename')
    mimetype = fields.Char('Mimetype',compute='_compute_mimetype', store=True)
    store_uuid = fields.Char('UUID')
    product_ids = fields.Many2many(comodel_name='product.product', column1='media_id',
                                 column2='product_id', string='Product Ids')
    shopware6_bind_ids = fields.One2many(
        comodel_name='shopware6.media.manager',
        inverse_name='openerp_id',
        string="Shopware6 Bindings",
    )
    is_shopware6_exported = fields.Boolean(string='Is Exported ?', compute='_get_is_shopware6_exported')

    @api.depends('data', 'filename', 'url', 'type')
    def _compute_mimetype(self):
        """ compute the mimetype of the given values
            :return mime : string indicating the mimetype, or application/octet-stream by default
        """
        for rec in self:
            self.mimetype = ''
            if rec.type == 'url' and rec.url:
                rec.mimetype = mimetypes.guess_type(rec.url)
            if rec.type == 'binary' and rec.data:
                rec.mimetype = guess_mimetype(base64.b64decode(rec.data))


    def _get_is_shopware6_exported(self):
        for this in self:
            this.is_shopware6_exported = False
            for bind in this.shopware6_bind_ids:
                if bind.shopware6_id:
                    this.is_shopware6_exported = True
                    pass

    def export_to_shopware6(self):
        self.ensure_one()
        backends = self.env['shopware6.backend'].search([])
        for backend in backends:
            product_bind = backend.create_bindings_for_model(self, 'shopware6_bind_ids')
        return True

    def get_thumbnail(self):
        '''
            sudo pip3 install youtube_dl
            pip install git+https://github.com/Cupcakus/pafy
        '''
        self.ensure_one()
        if self.media_url:
            media_url = self.media_url
            video_code = False
            if 'youtube-nocookie' in media_url:
                video_code = media_url.split("/")[-1]
            else:
                video_code = media_url.split("v=")[-1].split("&")[0]
            if video_code:
                try:
                    image_link = pafy.new("https://www.youtube.com/watch?v=%s"%video_code).bigthumbhd
                    img_res = requests.get(image_link, stream=True)
                    self.data = base64.b64encode(img_res.content)
                    self.filename = "thumbnail.jpg"
                    self.media_url = "https://www.youtube-nocookie.com/embed/%s"%video_code
                except Exception as e:
                    raise ValidationError(e)
        return True

class Shopware6MediaManager(models.Model):
    _name = 'shopware6.media.manager'
    _inherit = 'shopware6.binding'
    _inherits = {'media.manager': 'openerp_id'}
    _description = 'Shopware6 Media Manager'


    openerp_id = fields.Many2one(comodel_name='media.manager',
                                 string='Media Id',
                                 required=True, ondelete='cascade')


class MediaManagerAdapter(Component):
    _name = 'shopware6.media.manager.adapter'
    _inherit = 'shopware6.adapter'
    _apply_on = 'shopware6.media.manager'

    _shopware_uri = 'api/v3/media/'

    def set_image(self, binding):
        """ Update records on the external system """
        file_extension = "jpg"
        try:
            file_extension = binding.filename.rsplit(".",1)[1]
        except:
            pass
        #if 'pdf' in file_extension: # As per the instruction from Tobias I have disable transfer of PDF file
        #    return True
        if not binding.store_uuid:
            binding.store_uuid = uuid.uuid4().hex[:8]
        file_name = slugify(str(binding.name)+binding.store_uuid)
        image_data = {}
        if binding.type == 'url':
            image_data["url"] = binding.url
            file_extension = "jpg"
        else:
            image_data = base64.decodebytes(binding.data)

        shopware_uri = "api/v2/_action/media/%s/upload?extension=%s&fileName=%s" % (binding.shopware6_id, file_extension, file_name)
        _logger.info("Calling url from media maneger ===> %s"%shopware_uri)

        return self._call('POST', shopware_uri, image_data)

    def get_assigned_products(self, id):
        result = self._call('GET', self._shopware_uri + id + "/product-media")
        return result.get('data', result)

    def create_product_media(self, data):
        return self._call('POST', 'api/v3/product-media/', data)


class Shopware6MediaManager(Component):
    _name = 'shopware6.media.manager.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['shopware6.media.manager']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        record.with_delay().export_record()

class MediaManagerListener(Component):
    _name = 'media.manager.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['media.manager']

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