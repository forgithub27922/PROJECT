# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import base64

from collections import defaultdict
from slugify import slugify

from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.queue_job.job import job, related_action

_logger = logging.getLogger(__name__)


class ProductImage(models.Model):
    _inherit = 'product.image'

    shopware6_bind_ids = fields.One2many(
        comodel_name='shopware6.product.media',
        inverse_name='openerp_id',
        string="Shopware6 Bindings",
    )

    set_as_cover = fields.Boolean('Set as Cover ?')
    file_select = fields.Char(string="Upload Option", default="upload")
    # file_select = fields.Selection(string='Upload Option', selection=[('upload', 'Upload File'),('base', 'Base')], required=True,
    #                                default='upload')
    file_url = fields.Char('File URL')
    image = fields.Binary("Shopware6 Image", attachment=True, help="Shopware6 Image.", )

    shopware6_media_file_bind_ids = fields.One2many(
        comodel_name='shopware6.product.media.file',
        inverse_name='openerp_id',
        string="Shopware6 Media File",
    )
    is_shopware_exported = fields.Boolean(string='Is Exported ?', compute='_get_is_shopware_exported')
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product Id',
        help='Product ID',
        ondelete='cascade'
    )
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
            try:
                img_binding = backend.create_bindings_for_model(self, 'shopware6_bind_ids')
                img_binding.export_record()
                img_binding = backend.create_bindings_for_model(self, 'shopware6_media_file_bind_ids')
                img_binding.export_record()
            except:
                pass
        return True

    def remove_all_image_binding(self):
        self.ensure_one()
        # for binding in self.shopware6_bind_ids:
        #     target_shopware_id = getattr(binding, 'shopware6_id')
        #     if target_shopware_id:
        #         binding.with_delay().export_delete_record(binding.backend_id, target_shopware_id)
        # for binding in self.shopware6_media_file_bind_ids:
        #     target_shopware_id = getattr(binding, 'shopware6_id')
        #     if target_shopware_id:
        #         binding.with_delay().export_delete_record(binding.backend_id, target_shopware_id)
        self._cr.execute("DELETE FROM  shopware6_product_media WHERE openerp_id=%s;" % (self.id))
        self._cr.execute("DELETE FROM  shopware6_product_media_file WHERE openerp_id=%s;" % (self.id))
        self.export_to_shopware_media()
        return True

class Shopware6ProductMedia(models.Model):
    _name = 'shopware6.product.media'
    _inherit = 'shopware6.product.media'
    _inherits = {'product.image': 'openerp_id'}
    _description = 'Shopware6 Product Media'

    openerp_id = fields.Many2one(comodel_name='product.image',
                                 string='Product Media',
                                 required=True, ondelete='cascade')

class Shopware6ProductMediaFile(models.Model):
    _name = 'shopware6.product.media.file'
    _inherit = 'shopware6.product.media.file'
    _inherits = {'product.image': 'openerp_id'}
    _description = 'Shopware6 Product Media File'

    openerp_id = fields.Many2one(comodel_name='product.image',
                                 string='Product Media',
                                 required=True, ondelete='cascade')

class ProductMediaFileAdapter(Component):
    _name = 'shopware6.product.media.file.adapter'
    _inherit = 'shopware6.product.media.file.adapter'
    _apply_on = 'shopware6.product.media.file'

    _shopware_uri = 'api/v3/media/'

    def isBase64(self, s):
        try:
            return base64.b64encode(base64.b64decode(s)) == s
        except Exception:
            return False

    def _set_german_char(self, name=""):
        replace_list =[("Ü","ue"),("ü","ue"),("Ä","ae"),("ä","ae"),("Ö","oe"),("ö","oe")]
        for rl in replace_list:
            name = name.replace(rl[0],rl[1])
        return name

    def set_image(self, binding):
        """ Update records on the external system """
        # XXX actually only ol_catalog_product.update works
        # the PHP connector maybe breaks the catalog_product.update
        file_name_extension = [binding.openerp_id.product_id.default_code, ".jpg"]
        #if product_media.file_name:
        #    file_name_extension = os.path.splitext(product_media.file_name)
        import uuid

        image_file_name = "%s-%s"%(self._set_german_char(name=str(binding.openerp_id.product_id.name or binding.openerp_id.product_tmpl_id.name)),str(uuid.uuid4().hex[:5]))
        # file_name = slugify(str(binding.openerp_id.product_id.name or binding.openerp_id.product_tmpl_id.name) + str("-") + str(uuid.uuid4().hex[:5]))
        file_name = slugify(image_file_name)
        #shopware_uri = "api/v2/_action/media/%s/upload?extension=%s&fileName=%s"%(id,str(file_name_extension[1].replace(".","")),file_name_extension[0])
        shopware_uri = "api/v2/_action/media/%s/upload?extension=%s&fileName=%s" % (binding.shopware6_id, str(file_name_extension[1].replace(".", "")), file_name)
        #if binding.openerp_id.product_id:
        if binding.openerp_id.is_automatic_image:
            image_data = base64.decodestring(binding.openerp_id.automatic_image_data)
        else:
            image_data = base64.decodestring(binding.openerp_id.manual_image_data)
        # if binding.openerp_id.product_tmpl_id:
        #     if binding.openerp_id.file_select == 'base':
        #         image_data = binding.openerp_id.product_tmpl_id.image_1920
        #     else:
        #         image_data = binding.openerp_id.image

        if self.isBase64(image_data):
            image_data = base64.decodebytes(image_data)

        return self._call('POST', shopware_uri, image_data)

class ProductImageListener(Component):
    _name = 'shopware6.product.image.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['product.image']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        for shopware_bind in record.shopware6_media_file_bind_ids:
            shopware_bind.with_delay().export_record(fields=fields)
        for shopware_bind in record.shopware6_bind_ids:
            shopware_bind.with_delay().export_record(fields=fields)

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