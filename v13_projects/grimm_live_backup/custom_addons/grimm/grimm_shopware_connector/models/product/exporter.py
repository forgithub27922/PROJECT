# -*- coding: utf-8 -*-

import copy

from odoo import _
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo.addons.connector_magento.components.mapper import  normalize_datetime
from odoo.addons.connector.components.mapper import (only_create, changed_by, mapping)
import requests
import json

import logging

_logger = logging.getLogger(__name__)


class ProductTemplateExportMapper(Component):
    _name = 'shopware.product.template.export.mapper'
    _inherit = 'shopware.product.template.export.mapper'
    _apply_on = ['shopware.product.template']

    @mapping
    def map_supplier_info(self, record):
        supplier_id = ""
        if record.product_brand_id:
            for bind in record.product_brand_id.shopware_brand_ids:
                supplier_id = int(bind.shopware_id)
        if record.default_code.upper().startswith("GEV-"): #Added changes if article is GEV then supplier will be Partenics
            supplier_id = 28
        if supplier_id:
            return {"supplierId": supplier_id}

    @mapping
    def map_pseudoSales(self, record):
        return {"pseudoSales": 3} if record.is_photo_done or record.shopware_image_ids else {"pseudoSales": 0}

    @mapping
    def map_avoid_customer_group(self, record):
        if record.calculated_magento_price <= 0:
            return {"customerGroups": [{
                    "id": 3
            }]}
        else:
            return {"customerGroups": []}

    @mapping
    def map_attributes_value(self, record):
        res = super(ProductTemplateExportMapper, self).map_attributes_value(record)
        attribute_dict = res.get("attribute", {})
        attribute_dict.update({"isDevice": record.is_device})
        if record.is_device:
            attribute_dict.update({"grimmProductSku": record.default_code if record.magento_product_status_id.id == 1 and not record.should_export else ""}) #Added this change as suggestion from Tobias :)
        attribute_dict.update({"genuine": record.genuine})
        attribute_dict.update({"typeNumber": record.spare_part_option})
        if record.calculated_magento_price <= 0 or record.price_on_request:
            attribute_dict.update({"priceOnRequest": True})
        else:
            attribute_dict.update({"priceOnRequest": False})
        res["attribute"] = attribute_dict
        return res

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
                if attr.attribute_id.id != 878: # Added related to OD-941
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

    @mapping
    def map_product_maindata(self, record):
        res = super(ProductTemplateExportMapper, self).map_product_maindata(record)
        supplier_number = []
        if record.manufacture_code:
            supplier_number.append(record.manufacture_code)
        #shopware_backends = self.env['shopware.backend'].search([])[0]
        for supp in record.variant_seller_ids.filtered(lambda r: r.company_id.id == record.backend_id.default_company_id.id):
            if supp.product_code:
                split_code = supp.product_code.split("-", 1)
                if len(split_code) >= 2:
                    if not split_code[0].isdigit():
                        supplier_number.append(split_code[1])
                else:
                    supplier_number.append(supp.product_code)
        new_vals = {
            "unitId": 9,
            "purchaseUnit": record.shopware_package_content if record.shopware_package_content > 1 else 0,
            "referenceUnit": record.shopware_basic_unit if record.shopware_basic_unit > 1 else 0,
            "packUnit": record.shopware_packaging_unit,
            "ean": record.ean_number,
            "shippingTime": "1 - 3 Tage",
            "inStock": 1000,
            "supplierNumber": ', '.join(supplier_number) if (record.default_code and not record.default_code.upper().startswith("GEV-")) else "",
            "prices": [
                {
                    "customerGroupKey": 'EK',
                    "price": record.calculated_magento_price if record.calculated_magento_price > 0 else 0.01,
                    "from": 1,
                    #"to": 100,
                }
            ]
        }
        if res.get("mainDetail"):
            res.get("mainDetail").update(new_vals)
        else:
            res = {"mainDetail": new_vals}
        return res

class ShopwareProductTemplateExporter(Component):
    _name = 'shopware.product.template.exporter'
    _inherit = 'shopware.product.template.exporter'
    _apply_on = ['shopware.product.template']
    _usage = 'record.exporter'

    def _get_removable_link(self, existed_dict, check_link, code):
        remove_link = list(set(list(set([int(row['rel_product_id']) for row in existed_dict if row.get("code") == code]) - set(check_link))))
        add_link = list(set(check_link) - set(list(set([int(row['rel_product_id']) for row in existed_dict if row.get("code") == code]))))
        return {"remove":remove_link, "add": add_link}


    def _after_export(self):
        super(ShopwareProductTemplateExporter, self)._after_export()
        binding = self.binding

        existed_link = []
        try:
            existed_link = self.backend_adapter.search_product_link(binding.shopware_id)
        except:
            _logger.info("Get product assignment call is failed...")

        accessory_link = []
        for accessory in binding.openerp_id.accessory_part_ids:
            for p_ids in accessory.accessory_part_id.shopware_bind_ids:
                if p_ids.shopware_id:
                    accessory_link.append(int(p_ids.shopware_id))

        part_link = []
        for part in binding.openerp_id.spare_part_prod_ids:
            for p_ids in part.spare_part_id.shopware_bind_ids:
                if p_ids.shopware_id:
                    part_link.append(int(p_ids.shopware_id))
        #accessory_op = self._get_removable_link(existed_link, accessory_link, 'equipment')
        #del_accessory = [int(row['id']) for row in existed_link if row.get("code") == 'equipment' and row.get("rel_product_id") in accessory_op.get("remove")]
        #add_accessory = accessory_op.get("add")
        part_link.extend(accessory_link)


        parts_op = self._get_removable_link(existed_link, part_link, 'spare-part')
        del_parts = [int(row['id']) for row in existed_link if row.get("code") == 'spare-part' and row.get("rel_product_id") in parts_op.get("remove")]
        add_parts = parts_op.get("add")

        for remove_id in list(set(del_parts)):
            is_removed = self.backend_adapter.remove_product_link(remove_id)

        #for link in accessory_link:
        #    link_dict = {}
        #    link_dict["articleId"] = binding.shopware_id
        #    link_dict["relatedArticleId"] = link
        #    link_dict["code"] = "equipment"
        #    if int(link) in add_accessory:
        #        is_assigned = self.backend_adapter.assign_product_link(link_dict)
        for link in part_link:
            link_dict = {}
            link_dict["articleId"] = binding.shopware_id
            link_dict["relatedArticleId"] = link
            link_dict["code"] = "spare-part"
            if int(link) in add_parts:
                is_assigned = self.backend_adapter.assign_product_link(link_dict)

    def _get_img_url(self,barcode):
        image_links = []
        req = requests.get("https://imageserver.partenics.de/odoo/%s?format=json" % barcode)
        if req.status_code == 200:
            response = json.loads(req.content.decode("utf-8"))
            for server_image in response.get("images", []):
                if server_image.get("type", "") == "image":
                    image_links.append(server_image.get("srcUrl", False))
        image_links = ['https://applersg.com/img/command-line/613/how-download-file-from-server-with-ssh-scp.png']
        return image_links

    def _get_magento_img_url(self,product):
        image_ids = []
        for img in product.image_ids:
            image_ids.append(img.id)
        return image_ids

    def _export_dependency(self,binding):
        for image in binding.openerp_id.shopware_image_ids:
            img_binding = binding.backend_id.create_bindings_for_model(image, 'shopware_bind_ids')
        if binding.openerp_id.product_brand_id:
            brand_bind = binding.backend_id.create_bindings_for_model(binding.openerp_id.product_brand_id,
                                                           'shopware_brand_ids')
        if binding.openerp_id.property_set_id:
            export_property = binding.backend_id.create_bindings_for_model(binding.openerp_id.property_set_id,
                                                                'shopware_binding_ids')
        return True

        '''
        backends = self.env['shopware.backend'].search([])
        for backend in backends:

            if binding.openerp_id.is_device and binding.openerp_id.image_ids and not binding.openerp_id.is_image_on_server:
                images = self._get_magento_img_url(binding.openerp_id)

                for shopware_img in binding.openerp_id.shopware_image_ids.filtered(lambda r: r.record_inserted == "magento"):
                    if shopware_img.magento_image_id and shopware_img.magento_image_id.id not in images:
                        shopware_img.with_context(allow=True).unlink()

                for img in images:
                    avail_images = binding.openerp_id.shopware_image_ids.filtered(lambda r: r.record_inserted == "magento" and r.magento_image_id.id == img)
                    if not avail_images:
                        new_image_id = self.env["odoo.product.image"].create({"name":binding.openerp_id.name, 'file_select':'upload','magento_image_id':img, 'record_inserted':'magento', 'product_tmpl_id':binding.openerp_id.id})
                        _logger.info("NEW Magento RECORD IS ======================>>>>> ", new_image_id)
            else:
                for shopware_img in binding.openerp_id.shopware_image_ids.filtered(lambda r: r.record_inserted == "magento"):
                    shopware_img.with_context(allow=True).unlink()

            if not binding.openerp_id.is_image_on_server:
                for image in binding.openerp_id.shopware_image_ids:
                    img_binding = backend.create_bindings_for_model(image, 'shopware_bind_ids')

            if binding.openerp_id.product_brand_id:
                brand_bind = backend.create_bindings_for_model(binding.openerp_id.product_brand_id, 'shopware_brand_ids')
            if binding.openerp_id.property_set_id:
                export_property = backend.create_bindings_for_model(binding.openerp_id.property_set_id, 'shopware_binding_ids')
        return True
        '''