# -*- coding: utf-8 -*-

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.connector.components.mapper import (only_create, changed_by, mapping)

class ProductExportMapper(Component):
    _name = 'shopware.product.product.export.mapper'
    _inherit = 'shopware.export.mapper'
    _apply_on = ['shopware.product.product']

    direct = [
        ('name', 'name'),
        ('shopware_meta_description', 'description'),
        ('shopware_meta_description', 'descriptionLong'),
        ('status_on_shopware', 'active'),
        ('shopware_meta_keyword', 'keywords'),
        ('shopware_meta_title', 'metaTitle'),
        ('shopware_meta_title', 'metaTitle'),
    ]

    @mapping
    def map_default_code(self, record):
        # return {'number':record.defaul_code if record.defaul_code else record.id}
        return {'number': record.barcode if record.barcode  else record.id}

    @mapping
    def map_article(self, record):
        article_dict = {}
        article_dict["mainDetailId"] = record.product_tmpl_id.main_detail_id
        supplier_id = ""
        if record.variant_seller_ids:
            seller = record.variant_seller_ids[0]
            for bind in seller.name.shopware_supplier_ids:
                supplier_id = int(bind.shopware_id)
        article_dict["supplierId"] = supplier_id
        if record.property_set_id:
            for property in record.property_set_id.shopware_binding_ids:
                property_id = property.shopware_id
                article_dict["filterGroupId"] = supplier_id
        return {"article": article_dict}



class ShopwareProductExporter(Component):
    _name = 'shopware.product.product.exporter'
    _inherit = 'shopware.exporter'
    _apply_on = ['shopware.product.product']
    _usage = 'record.exporter'

    def __init__(self, connector_env):
        super(ShopwareProductExporter, self).__init__(connector_env)
        self.storeview_id = None
        self.link_to_parent = False
        self.fields = None

    def _export_dependency(self,binding):
        for image in binding.openerp_id.shopware_image_ids:
            img_binding = binding.backend_id.create_bindings_for_model(image, 'shopware_bind_ids')
        if binding.openerp_id.seller_ids:
            supplier = binding.openerp_id.seller_ids[0]
            supplier_bind = binding.backend_id.create_bindings_for_model(supplier.name, 'shopware_supplier_ids')
        return True


    def _should_import(self):
        return False

    def run(self, binding_id, *args, **kwargs):
        self._export_dependency(binding_id)
        self.fields = kwargs.get('fields', {})
        res = super(ShopwareProductExporter, self).run(binding_id, *args, **kwargs)
        return res

    def _after_export(self):
        '''
        This method will again execute read method for same product because we need image link ID from shopware
        so product will not add images with every request.
        :return:
        '''
        product_data = self.backend_adapter.read(int(self.binding.shopware_id))
        image_data = product_data.get('images')
        image_link = {}
        for image in image_data:
            image_link[str(image.get('mediaId'))] = {"id":image.get('id'),"articleId":image.get('articleId')}
        product_id = self.binding.openerp_id
        for image in product_id.shopware_image_ids:
            if image.shopware_id < 1:
                for media in image.shopware_bind_ids:
                    if image_link.get(media.shopware_id):
                        if int(self.binding.shopware_id) == int(image_link.get(media.shopware_id).get("articleId")):
                            #instead of ORM update executed direct SQL otherwise odoo connector will send this product to update on shopware due to on_record_write call
                            self.env.cr.execute("update odoo_product_image set shopware_id=%s where id=%s;",(int(image_link.get(media.shopware_id).get("id")),int(image.id),))

class ProductProductDeleter(Component):
    _name = 'shopware.product.product.exporter.deleter'
    _inherit = 'shopware.exporter.deleter'
    _apply_on = ['shopware.product.product']
    _usage = 'record.exporter.deleter'