# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2016 Openfellas (http://openfellas.com) All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly advised to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################


import base64
from tempfile import TemporaryFile

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.connector.components.mapper import (changed_by, mapping)
from odoo.tools.translate import _

from .. import magic
from ...constants import NO_IMAGES_SYNC


class CatalogImageExportMapper(Component):
    _name = 'magento.product.image.export.mapper'
    _inherit = 'magento.export.mapper'
    _apply_on = ['magento.product.image']

    def prepare_binary_data(self, record):

        if record.is_automatic_image:
            image_data = record.automatic_image_data
        else:
            image_data = record.manual_image_data

        with TemporaryFile() as f:
            f.write(base64.b64decode(image_data))
            f.seek(0)
            file_data = f.read()

            ms = magic.open(magic.MAGIC_MIME)
            ms.load()

            mime = ms.buffer(file_data)

        name = record.file_name or ''

        try:
            if mime:
                mime = mime.split(';')[0]
                name = name.replace('.' + mime.split('/')[1], '')
        except:
            pass

        return {
            'mime': mime,
            'content': image_data,
            'name': name,
        }

    @changed_by('is_base_image', 'is_small_image', 'is_thumbnail')
    @mapping
    def image_types(self, record):
        res = {}

        types = []

        if record.is_base_image:
            types.append('image')

        if record.is_small_image:
            types.append('small_image')

        if record.is_thumbnail:
            types.append('thumbnail')

        if types:
            res['types'] = types

        return res

    @changed_by('name', 'position')
    @mapping
    def image_label_pos(self, record):
        res = {
            'label': record.name,
            'position': record.position
        }

        return res

    @changed_by('manual_image_data', 'binary_write_date')
    @mapping
    def image_file(self, record):
        binary_data = self.prepare_binary_data(record)

        res = {
            'file': {
                'content': binary_data['content'],
                'mime': binary_data['mime'],
                'name': binary_data['name'],
            },
            'exclude': False,
        }

        return res


class ProductImageExporter(Component):
    _name = 'magento.product.image.exporter'
    _inherit = 'magento.exporter'
    _apply_on = ['magento.product.image']
    _usage = 'record.exporter'

    def get_magento_product_id(self):
        magento_product_id = False

        if self.binding.magento_product_id:
            magento_product_id = self.binding.magento_product_id.magento_id
        elif self.binding.magento_ptmpl_id:
            magento_product_id = self.binding.magento_ptmpl_id.magento_id

        return magento_product_id

    def _get_magento_id(self):
        product_tmpl_id = self.binding.openerp_id.product_tmpl_id
        for ptmpl_binding in product_tmpl_id.magento_pp_bind_ids.filtered(lambda rec: rec.backend_id.id == self.binding.backend_id.id):
            return ptmpl_binding.magento_id # If magento_id found from here it will return else check for ptmpl_bind_ids

        for ptmpl_binding in product_tmpl_id.magento_ptmpl_bind_ids.filtered(lambda rec: rec.backend_id.id == self.binding.backend_id.id):
            return ptmpl_binding.magento_id

    def _create(self, data):
        magento_product_id = self.get_magento_product_id()
        if not magento_product_id:
            magento_product_id = self._get_magento_id()
        res = self.backend_adapter.create(magento_product_id, data)
        return res

    def _update(self, data):
        assert self.magento_id
        magento_product_id = self.get_magento_product_id()
        if not magento_product_id:
            magento_product_id = self._get_magento_id()
        res = self.backend_adapter.write(magento_product_id, self.magento_id, data)
        return res

    def _should_import(self):
        return False


class ProductImageDeleter(Component):
    _name = 'magento.product.product.exporter.deleter'
    _inherit = 'magento.exporter.deleter'
    _apply_on = ['magento.product.image']
    _usage = 'record.exporter.deleter'

    def run(self, magento_image_id, product_id):
        self.backend_adapter.delete(product_id, magento_image_id)
        return _('Record %s deleted on Magento') % magento_image_id


class ProductImageListener(Component):
    _name = 'product.image.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['product.image']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        return True # magento_stop
        for binding in record.magento_binding_ids:
            if binding.backend_id.product_images_export_type == NO_IMAGES_SYNC:
                continue
            if record._is_product_exported(binding.backend_id):
                binding.with_delay().export_record(fields=fields)
        return True

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_unlink(self, record):
        return True # magento_stop
        for binding in record.magento_binding_ids:
            if binding.backend_id.product_images_export_type == NO_IMAGES_SYNC:
                continue
            magento_product_id = getattr(getattr(binding,
                                                 'magento_product_id',
                                                 getattr(binding, 'magento_ptmpl_id', {})
                                                 ),
                                         'magento_id', None)
            if magento_product_id:
                binding.with_delay().export_delete_record(binding.backend_id, binding.magento_id, magento_product_id)


class MagentoProductImageListener(Component):
    _name = 'magento.product.image.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['magento.product.image']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        return True # magento_stop
        for binding in record.magento_binding_ids:
            if binding.backend_id.product_images_export_type == NO_IMAGES_SYNC:
                continue
            if record._is_product_exported(binding.backend_id):
                binding.with_delay().export_record(fields=fields)
        return True

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        return True # magento_stop
        backend = record.backend_id

        if backend.product_images_export_type == NO_IMAGES_SYNC:
            return False
        if record.openerp_id._is_product_exported(backend):
            record.with_delay().export_record()
#
# # @on_record_create(model_names='magento.product.image')
# def export_magento_image(session, model_name, record_id, vals):
#     if session.context.get('connector_no_export', False):
#         return False
#
#     record = session.env[model_name].browse(record_id)
#     backend = record.backend_id
#
#     if backend.product_images_export_type == NO_IMAGES_SYNC:
#         return False
#
#     if record.openerp_id._is_product_exported(backend):
#         export_record.delay(session, model_name, record_id, vals)
#
#     return True


# @on_record_write(model_names='product.image')
# def update_image_on_magento(session, model_name, record_id, fields=None):
#     if session.context.get('connector_no_export'):
#         return False
#
#     record = session.env[model_name].browse(record_id)
#
#     for binding in record.magento_binding_ids:
#         if binding.backend_id.product_images_export_type == NO_IMAGES_SYNC:
#             continue
#
#         if record._is_product_exported(binding.backend_id):
#             export_record.delay(session, binding._name, binding.id, fields)
#
#     return True
#
#
# @on_record_unlink(model_names='product.image')
# def delete_image_on_magento(session, model_name, record_id):
#     record = session.env[model_name].browse(record_id)
#     magento_product_id = False
#
#     for binding in record.magento_binding_ids:
#         if binding.backend_id.product_images_export_type == NO_IMAGES_SYNC:
#             continue
#
#         if binding.magento_id:
#             if binding.magento_product_id:
#                 magento_product_id = binding.magento_product_id.magento_id
#             elif binding.magento_ptmpl_id:
#                 magento_product_id = binding.magento_ptmpl_id.magento_id
#
#             if magento_product_id:
#                 delete_image.delay(session, binding._name, binding.backend_id.id, binding.magento_id,
#                                    magento_product_id)
#
#     return True
#
#
# @job(default_channel='root.magento')
# def delete_image(session, model_name, backend_id, magento_image_id, magento_product_id):
#     """Remove product image on Magento"""
#
#     env = get_environment(session, model_name, backend_id)
#     deleter = env.get_connector_unit(ProductImageDeleter)
#     return deleter.run(magento_image_id, magento_product_id)
