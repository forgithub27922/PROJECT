# -*- coding: utf-8 -*-

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.connector.components.mapper import (only_create, changed_by, mapping)
import logging
_logger = logging.getLogger(__name__)

class ProductMediaMapper(Component):
    _name = 'shopware6.product.media.export.mapper'
    _inherit = 'shopware6.export.mapper'
    #_apply_on = ['shopware6.product.template']
    _apply_on = ['shopware6.product.media']

    direct = [
        ('name', 'name')
    ]

    @mapping
    def assign_media_file(self, record):
        return_dict = {}
        has_variant = False
        product_template = record.openerp_id.product_id.product_tmpl_id
        product_product = record.openerp_id.product_id


        if record.openerp_id.product_tmpl_id:
            for product in record.openerp_id.product_tmpl_id.shopware6_bind_ids:
                return_dict['productId'] = product.shopware6_id
            for product in record.openerp_id.product_tmpl_id.shopware6_pt_bind_ids:
                return_dict['productId'] = product.shopware6_id
        else:
            for product in record.openerp_id.variant_product_id.shopware6_bind_ids:
                return_dict['productId'] = product.shopware6_id
        return_dict["position"] = record.position if record.position else 0





        # if record.openerp_id.product_tmpl_id:
        #     for product in record.openerp_id.product_tmpl_id.shopware6_pt_bind_ids:
        #         return_dict['productId'] = product.shopware6_id
        # else:
        #     for product in record.openerp_id.product_id.shopware6_bind_ids:
        #         return_dict['productId'] = product.shopware6_id
        for media in record.openerp_id.shopware6_media_file_bind_ids:
            return_dict['mediaId'] = media.shopware6_id

        return return_dict

class ProductMediaFileMapper(Component):
    _name = 'shopware6.product.media.file.export.mapper'
    _inherit = 'shopware6.export.mapper'
    #_apply_on = ['shopware6.product.template']
    _apply_on = ['shopware6.product.media.file']

    direct = [
        ('name', 'name'),
    ]

    @mapping
    def set_parent_folder(self, record):
        return_res = {}
        for binding in record.openerp_id.product_id.shopware6_bind_ids:
            backend = binding.backend_id
            if backend.default_media_folder_id and backend.default_media_folder_id.shopware6_bind_ids[0].shopware6_id:
                return_res["mediaFolderId"] = backend.default_media_folder_id.shopware6_bind_ids[0].shopware6_id
        return return_res


class Shopware6ProductMediaExporter(Component):
    _name = 'shopware6.product.media.exporter'
    _inherit = 'shopware6.exporter'
    _apply_on = ['shopware6.product.media']
    _usage = 'record.exporter'

    def _export_dependency(self,binding):
        export_property = binding.backend_id.create_bindings_for_model(binding.openerp_id, 'shopware6_media_file_bind_ids')
        return True

    def run(self, binding_id, *args, **kwargs):
        self._export_dependency(binding_id)
        self.fields = kwargs.get('fields', {})
        res = super(Shopware6ProductMediaExporter, self).run(binding_id, *args, **kwargs)
        return res

    def _after_export(self):
        cover_index = 0
        if self.binding.openerp_id.variant_product_id:
            iterate_field = self.binding.openerp_id.variant_product_id.shopware6_bind_ids
            for image_data in self.binding.openerp_id.variant_product_id.variant_image_ids:
                if image_data.set_as_cover and image_data.shopware6_bind_ids:
                    self.backend_adapter.set_as_cover(iterate_field[0].shopware6_id,{"coverId": image_data.shopware6_bind_ids[0].shopware6_id})
                    break
                elif cover_index == 0 and image_data.shopware6_bind_ids:
                    self.backend_adapter.set_as_cover(iterate_field[0].shopware6_id,{"coverId": image_data.shopware6_bind_ids[0].shopware6_id})
                    cover_index = 1

        if self.binding.openerp_id.product_tmpl_id:
            iterate_field = self.binding.openerp_id.product_tmpl_id.shopware6_pt_bind_ids
            if self.binding.openerp_id.product_tmpl_id.product_variant_count == 1:
                iterate_field = self.binding.openerp_id.product_tmpl_id.shopware6_bind_ids

            for image_data in self.binding.openerp_id.product_tmpl_id.image_ids:
                if image_data.set_as_cover and image_data.shopware6_bind_ids:
                    self.backend_adapter.set_as_cover(iterate_field[0].shopware6_id,{"coverId": image_data.shopware6_bind_ids[0].shopware6_id})
                    break
                elif cover_index == 0 and image_data.shopware6_bind_ids:
                    self.backend_adapter.set_as_cover(iterate_field[0].shopware6_id,{"coverId": image_data.shopware6_bind_ids[0].shopware6_id})
                    cover_index = 1

            # for product_media in iterate_field:
            #     if cover_index == 0:
            #         self.backend_adapter.set_as_cover(product_media.shopware6_bind_ids[0].shopware6_id,{"coverId": self.binding.shopware6_id})
            #         cover_index = 1
            #     elif self.binding.set_as_cover or binding.is_base_image:
            #         self.backend_adapter.set_as_cover(product_media.shopware6_id,{"coverId": self.binding.shopware6_id})

        pass

class Shopware6ProductMediaFileExporter(Component):
    _name = 'shopware6.product.media.file.exporter'
    _inherit = 'shopware6.exporter'
    _apply_on = ['shopware6.product.media.file']
    _usage = 'record.exporter'

    def _export_dependency(self,binding):
        # if binding.openerp_id.parent_id:
        #     export_media_file = binding.backend_id.create_bindings_for_model(binding.openerp_id.parent_id, 'shopware6_bind_ids')
        #     export_media_file.export_record()
        return True

    def run(self, binding_id, *args, **kwargs):
        #self._export_dependency(binding_id)
        self.fields = kwargs.get('fields', {})
        res = super(Shopware6ProductMediaFileExporter, self).run(binding_id, *args, **kwargs)
        return res

    def _after_export(self):
        config_setting = self.backend_adapter.set_image(self.binding)
        pass
class ProductMediaDeleter(Component):
    _name = 'shopware6.product.media.exporter.deleter'
    _inherit = 'shopware6.exporter.deleter'
    _apply_on = ['shopware6.product.media','shopware6.product.media.file']
    _usage = 'record.exporter.deleter'