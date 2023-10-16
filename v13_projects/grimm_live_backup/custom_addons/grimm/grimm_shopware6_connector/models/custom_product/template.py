# -*- coding: utf-8 -*-
# Copyright 2013-2017 Camptocamp SA
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
from slugify import slugify
import hashlib
import base64
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
import logging
_logger = logging.getLogger(__name__)


class CustomProductTemplate(models.Model):
    _name = 'grimm_custom_product.template'
    _description = 'Grimm Custom Product Template'

    name = fields.Char(required=True)
    technical_name = fields.Char(compute='_compute_technical_name', store=True)
    description = fields.Html()
    shopware6_media_id = fields.Char("Shopware6 Media Id")
    active = fields.Boolean()
    step_by_step_mode = fields.Boolean()
    options_auto_collapse = fields.Boolean()
    need_confirmation = fields.Boolean()
    image = fields.Binary("Image", attachment=True, help="Custom Product Image.", )
    option_ids = fields.One2many('grimm_custom_product.option', 'template_id')
    shopware6_bind_ids = fields.One2many(
        comodel_name='shopware6.grimm_custom_product.template',
        inverse_name='openerp_id',
        string='Shopware6 Bindings',
    )
    is_shopware6_exported = fields.Boolean(string='Is Exported ?', compute='_get_is_shopware6_exported')

    def _get_is_shopware6_exported(self):
        for this in self:
            this.is_shopware6_exported = False
            for bind in this.shopware6_bind_ids:
                if bind.shopware6_id:
                    this.is_shopware6_exported = True

    @api.depends('name')
    def _compute_technical_name(self):
        for this in self:
            if this.id:
                this.technical_name = hashlib.md5(
                    str(this.id).encode('utf-8')).hexdigest()[:5] \
                                      + "-" \
                                      + \
                                      (slugify(this.name))[:20]

    def export_to_shopware6(self):
        self.ensure_one()
        backends = self.env['shopware6.backend'].search([])
        for backend in backends:
            product_bind = backend.create_bindings_for_model(self, 'shopware6_bind_ids')
        return True

class CustomProductTemplateShopware6(models.Model):
    _name = 'shopware6.grimm_custom_product.template'
    _inherit = 'shopware6.binding'
    _inherits = {'grimm_custom_product.template': 'openerp_id'}
    _description = 'Shopware6 Custom Product'

    _rec_name = 'backend_id'

    openerp_id = fields.Many2one(comodel_name='grimm_custom_product.template',
                                 string='Custom Product',
                                 required=True,
                                 ondelete='cascade')

class Shopware6BindingCustomProductTemplateListener(Component):
    _name = 'shopware6.binding.custom.product.template.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['shopware6.grimm_custom_product.template']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        record.export_record()

class Shopware6CustomProductTemplateListener(Component):
    _name = 'custom.product.template.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['grimm_custom_product.template']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        for pp_bind in record.shopware6_bind_ids:
            pp_bind.with_delay().export_record(fields=fields)

class CustomProductTemplateAdapter6(Component):
    _name = 'shopware6.grimm_custom_product.template.adapter'
    _inherit = 'shopware6.adapter'
    _apply_on = 'shopware6.grimm_custom_product.template'

    _shopware_uri = 'api/v3/swag-customized-products-template/'

    def create_assign_media(self, binding):
        if not binding.openerp_id.shopware6_media_id:
            backend = binding.backend_id
            media_res = {}
            media_res["name"] = binding.openerp_id.technical_name
            if backend.default_media_folder_id and backend.default_media_folder_id.shopware6_bind_ids[0].shopware6_id:
                media_res["mediaFolderId"] = backend.default_media_folder_id.shopware6_bind_ids[0].shopware6_id
            shopware_uri = 'api/v3/media/'
            created_media =  self._call('POST', shopware_uri, media_res)
            binding.openerp_id.shopware6_media_id = created_media

        if binding.openerp_id.shopware6_media_id:
            file_name_extension = [binding.openerp_id.technical_name, ".jpg"]
            import uuid
            shopware_uri = "api/v2/_action/media/%s/upload?extension=%s&fileName=%s" % (binding.shopware6_media_id, str(file_name_extension[1].replace(".", "")), file_name_extension[0])
            image_data = binding.openerp_id.image
            self._call('POST', shopware_uri, base64.decodebytes(image_data))
            self._call('PATCH', '%s%s' % (self._shopware_uri, binding.shopware6_id), {"mediaId":binding.openerp_id.shopware6_media_id})