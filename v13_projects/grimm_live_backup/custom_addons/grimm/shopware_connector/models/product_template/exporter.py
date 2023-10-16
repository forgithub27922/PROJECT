# -*- coding: utf-8 -*-

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.connector.components.mapper import (only_create, changed_by, mapping)
from odoo.addons.queue_job.exception import NothingToDoJob, FailedJobError

class ProductTemplateExportMapper(Component):
    _name = 'shopware.product.template.export.mapper'
    _inherit = 'shopware.export.mapper'
    _apply_on = ['shopware.product.template']

    direct = [
        ('name', 'name'),
        ('shopware_meta_description', 'description'),
        ('shopware_description', 'descriptionLong'),
        ('status_on_shopware', 'active'),
        ('shopware_meta_keyword', 'keywords'),
        ('shopware_meta_title', 'metaTitle'),
    ]

    @changed_by('shopware_categories')
    @mapping
    def map_supplier_info(self, record):
        supplier_id = ""
        if record.seller_ids:
            seller = record.seller_ids[0]
            for bind in seller.name.shopware_supplier_ids:
                supplier_id = int(bind.shopware_id)
        if supplier_id:
            return {"supplierId": supplier_id}

    @mapping
    def map_attributes_value(self, record):
        '''
        Developer can inherit this method to set attribute based on their requirement.
        :param record:
        :return:
        '''
        return {}

    @changed_by('property_set_id', 'shopware_property_ids')
    @mapping
    def map_property(self, record):
        property_list = []
        return_map = {}
        property_id = False
        if record.property_set_id:
            for property in record.property_set_id.shopware_binding_ids:
                property_id = property.shopware_id
        if property_id:
            for attr in record.shopware_property_ids:
                for vals in attr.value_ids:
                    temp_dict = {}
                    temp_dict['option'] = {'name': attr.attribute_id.name}
                    temp_dict['value'] = vals.name
                    property_list.append(temp_dict)
            return_map = {
                "filterGroupId": property_id,
                "propertyValues": property_list
            }
        if property_list:
            detail_list = []
            for var in record.product_variant_ids:
                temp_dict = {}
                temp_dict["number"] = var.id
            # return_map["details"] = detail_list

        return return_map

    @changed_by('shopware_image_ids')
    @mapping
    def map_images(selfself, record):
        image_list = []
        for data in record.shopware_image_ids:
            for img in data.shopware_bind_ids:
                temp_dict = {
                    "description": data.name,
                    "main": 1,
                    "position": data.position,
                    "mediaId": int(img.shopware_id)
                }
                if data.shopware_id and record.is_shopware_exported:
                    temp_dict['id'] = int(data.shopware_id)
                image_list.append(temp_dict)
        if image_list:
            return {
                "images": image_list
            }
        else:
            {}

    @changed_by('shopware_categories')
    @mapping
    def map_category(selfself, record):
        categ_list = []
        for categ in record.shopware_categories:
            for shopware_categ in categ.shopware_bind_ids:
                categ_list.append({"id": int(shopware_categ.shopware_id)})
        return {
            "categories": categ_list,
        }

    @changed_by('status_on_shopware')
    @mapping
    def map_active(selfself, record):
        return {
            "active": record.status_on_shopware,
        }

    #@changed_by('taxes_id')
    @mapping
    def map_product_tax(self, record):
        if record.sudo().taxes_id:
            taxes = record.sudo().taxes_id.filtered(lambda r: r.company_id.sudo().id == record.backend_id.sudo().default_company_id.id)
            for tax in taxes:
                for shop_tax in record.backend_id.sudo().tax_mapping_ids:
                    if shop_tax.tax_id.id == tax.id:
                        tax_data = {"tax": {
                            "tax": shop_tax.shopware_tax_percent,
                            "name": shop_tax.tax_id.name
                        }}
                        return tax_data
            raise FailedJobError("No Tax mapping is available for %s tax. Please add mapping in Shopware Backend.\n\n" % (taxes.name))


    @mapping
    def map_product_maindata(self, record):
        supplier_number = []
        for supp in record.variant_seller_ids.filtered(lambda r: r.company_id.id == record.backend_id.default_company_id.id):
            if supp.product_code:
                supplier_number.append(supp.product_code)
        main_data = {
            "mainDetail": {
                "unitId": '',
                "active": record.status_on_shopware,
                "number": record.product_variant_id.barcode if record.product_variant_id.barcode else record.product_variant_id.default_code,
                "supplierNumber":', '.join(supplier_number),
                "prices": [
                        {
                            "customerGroupKey": 'EK',
                            "price": record.list_price,
                            "from": 1,
                            "to": 100,
                        }
                ]
            }
        }
        return main_data

class ShopwareProductTemplateExporter(Component):
    _name = 'shopware.product.template.exporter'
    _inherit = 'shopware.exporter'
    _apply_on = ['shopware.product.template']
    _usage = 'record.exporter'

    def _export_dependency(self,binding):
        for image in binding.openerp_id.shopware_image_ids:
            img_binding = binding.backend_id.create_bindings_for_model(image, 'shopware_bind_ids')
        if binding.openerp_id.seller_ids:
            supplier = binding.openerp_id.seller_ids[0]
            supplier_bind = binding.backend_id.create_bindings_for_model(supplier.name, 'shopware_supplier_ids')
        if binding.openerp_id.property_set_id:
            export_property = binding.backend_id.create_bindings_for_model(binding.openerp_id.property_set_id, 'shopware_binding_ids')
        return True

    def run(self, binding_id, *args, **kwargs):
        self._export_dependency(binding_id)
        self.fields = kwargs.get('fields', {})
        res = super(ShopwareProductTemplateExporter, self).run(binding_id, *args, **kwargs)
        return res

    def _after_export(self):
        '''
        This method will again execute read method for same product because we need image link ID from shopware
        so product will not add images with every request.
        :return:
        '''
        product_data = self.backend_adapter.read(int(self.binding.shopware_id))
        image_data = product_data.get('images', [])
        self.binding.created_at = product_data.get('added', '').replace("T", " ").split("+")[0]
        self.binding.updated_at = product_data.get('changed', '').replace("T", " ").split("+")[0]
        image_link = {}
        for image in image_data:
            image_link[str(image.get('mediaId'))] = {"id": image.get('id'), "articleId": image.get('articleId')}
        product_id = self.binding.openerp_id
        for image in product_id.shopware_image_ids:
            if not image.shopware_id or not product_id.is_shopware_exported:
                for media in image.shopware_bind_ids:
                    if image_link.get(media.shopware_id):
                        if int(self.binding.shopware_id) == int(image_link.get(media.shopware_id).get("articleId")):
                            #instead of ORM update executed direct SQL otherwise odoo connector will send this product to update on shopware due to on_record_write call
                            self.env.cr.execute("update odoo_product_image set shopware_id=%s where id=%s;",(int(image_link.get(media.shopware_id).get("id")),int(image.id),))

class ProductTemplateDeleter(Component):
    _name = 'shopware.product.template.exporter.deleter'
    _inherit = 'shopware.exporter.deleter'
    _apply_on = ['shopware.product.template']
    _usage = 'record.exporter.deleter'
