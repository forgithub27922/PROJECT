# -*- coding: utf-8 -*-

from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
from odoo.addons.connector.components.mapper import (only_create, changed_by, mapping)
from odoo.tools.translate import _
from odoo.addons.connector_magento.components.backend_adapter import MagentoAPI # Added for sync package qty value
import logging
_logger = logging.getLogger(__name__)

from ...constants import (PRODUCTS_ODOO_MASTER, CONFIGURABLE_PRODUCT, CONFIGURABLE_TYPE, MULTISELECT_TYPE, TEXT_TYPE,
                          SIMPLE_TEXT_TYPE, SELECT_TYPE)


class ProductExportMapper(Component):
    _name = 'magento.product.product.export.mapper'
    _inherit = 'magento.export.mapper'
    _apply_on = ['magento.product.product']

    direct = [
        ('name', 'name'),
        ('default_code', 'sku'),
        ('description', 'short_description'),
        ('weight', 'weight'),
        #('description_sale', 'description'),
    ]

    @mapping
    def add_description(self, record):
        description = record.description
        if record.is_spare_part:
            description = "<h2>" + str(record.name) + "</h2><p><br></p><h3>Ausführung:</h3><ul class='decorate-list'>"
            for property in record.shopware_property_ids:
                if property.attribute_id.id != 878:  # Added related to OD-941
                    description += "<li>" + str(property.attribute_id.name) + ": " + str(
                        ", ".join([val.name for val in property.value_ids])) + "</li>"
            description += "</ul>"
        return {'description_sale': description}

    @only_create
    @mapping
    def type_id(self, record):
        return {
            'type_id': record.product_type
        }

    @only_create
    @mapping
    def team_webhook(self, record):
        if record.backend_id.team_webhook_url:
            return {
                'team_webhook':{
                    "Name" : record.name,
                    "SKU": record.default_code,
                    "Price ": "%s €"%(record.calculated_magento_price),
                    "Description": record.short_description,
                    "URL" : "%s/catalogsearch/result/?q=%s"%(record.backend_id.location, record.default_code),
                    "Exported By": "<a href='mailto:%s'>%s</a>"%(self.env.user.login,self.env.user.partner_id.name)
                }
            }
        else:
            return {}

    @changed_by('lst_price')
    @mapping
    def price(self, record):
        return {
            'price': record.lst_price
        }

    @changed_by('attribute_set_id')
    @mapping
    def set(self, record):
        res = {}
        if record.magento_attribute_set_id:
            res['set'] = record.magento_attribute_set_id.magento_id
        return res

    @only_create
    @mapping
    def categories(self, record):
        category_ids = []

        if record.magento_category_id and record.magento_category_id.magento_id:
            category_ids.append(int(record.magento_category_id.magento_id))
        elif self.backend_record.default_product_ctg_id:
            category_ids.append(int(self.backend_record.default_product_ctg_id))

        if len(category_ids) == 0:
            raise Warning(_('Product category is not properly set!'))

        return {'categories': category_ids}

    @only_create
    @mapping
    def websites(self, record):
        website_ids = []
        # binder = self.binder_for('magento.website')
        for website in self.backend_record.website_ids:
            # website_id = binder.to_backend(website.id)
            website_ids.append(website.magento_id)
        return {'websites': website_ids}

    @changed_by('active')
    @mapping
    def status(self, record):
        if record.active:
            return {'status': 1}
        return {'status': 2}

    @changed_by('attribute_data_ids')
    @mapping
    def visibility(self, record):
        res = self.env['product.template'].get_magento_visibility(record)
        return {'visibility': res}

    @only_create
    @mapping
    def system_attributes(self, record):
        to_skip = ['status', 'visibility']

        res = {
            # 'tax_class_id': DEFAULT_TAX_CLASS_ID,
        }

        for system_attr_val in self.backend_record.product_system_val_ids:
            attribute = system_attr_val.magento_attribute_id
            attribute_val = system_attr_val.magento_attr_value_id

            if not (attribute.magento_code and attribute_val.magento_id) or attribute.magento_code in to_skip:
                continue

            res[attribute.magento_code] = attribute_val.magento_id

        return res

    @changed_by('product_template_attribute_value_ids') #Odoo13Change
    @mapping
    def attributes(self, record):
        res = {}

        for attr_val_bind in record.magento_attribute_value_ids.filtered(
                lambda rec: rec.backend_id.id == self.backend_record.id):

            magento_attr_code = attr_val_bind.magento_attribute_id.magento_code
            magento_value_code = attr_val_bind.magento_id

            if magento_attr_code and magento_value_code:
                res[magento_attr_code] = magento_value_code

        return res

    @changed_by('attribute_data_ids')
    @mapping
    def additional_attributes(self, record):
        res = {}
        return res  # Commented as suggestions from Tobias.

        if not record.attribute_data_ids:
            return {}

        magento_attribute_set = record.magento_attribute_set_id

        for magento_attr in magento_attribute_set.magento_attribute_ids.filtered(
                lambda rec: rec.use_in_products == True and rec.type in (SELECT_TYPE, CONFIGURABLE_TYPE)):

            if not magento_attr.magento_id or magento_attr.magento_code == 'visibility':
                continue

            found = False

            for attr_data in record.attribute_data_ids.filtered(lambda rec: rec.attr_id.use_in_products == True):
                if attr_data.attr_id.id == magento_attr.openerp_id.id:
                    value_bind = attr_data.value_id.magento_binding_ids.filtered(
                        lambda rec: rec.magento_id and rec.backend_id.id == magento_attr.backend_id.id
                    )

                    if value_bind:
                        found = True
                        res[magento_attr.magento_code] = value_bind.magento_id

                    break

            if not found:
                res[magento_attr.magento_code] = 0

        return res

    @changed_by('textual_attribute_data_ids')
    @mapping
    def additional_textual_attributes(self, record):
        res = {}
        return res  # Commented as suggestions from Tobias.

        if not record.textual_attribute_data_ids:
            return {}

        magento_attribute_set = record.magento_attribute_set_id

        for magento_attr in magento_attribute_set.magento_attribute_ids.filtered(lambda rec: rec.use_in_products == True and rec.type in (TEXT_TYPE, SIMPLE_TEXT_TYPE)):

            if not magento_attr.magento_id:
                continue

            found = False

            for attr_data in record.textual_attribute_data_ids.filtered(
                    lambda rec: rec.attr_id.use_in_products == True):
                if attr_data.attr_id.id == magento_attr.openerp_id.id:
                    if attr_data.value_id:
                        found = True
                        res[magento_attr.magento_code] = attr_data.value_id

                    break

            if not found:
                res[magento_attr.magento_code] = ''

        return res

    @changed_by('attribute_data_multi_select_ids')
    @mapping
    def additional_multi_select_attributes(self, record):
        res = {}
        return res # Commented as suggestions from Tobias.

        if not record.attribute_data_multi_select_ids:
            return {}

        magento_attribute_set = record.magento_attribute_set_id

        for magento_attr in magento_attribute_set.magento_attribute_ids.filtered(
                lambda rec: rec.use_in_products == True and rec.type in (MULTISELECT_TYPE,)):

            if not magento_attr.magento_id or magento_attr.magento_code == 'visibility':
                continue

            res[magento_attr.magento_code] = []
            for attr_data in record.attribute_data_multi_select_ids.filtered(
                    lambda rec: rec.attr_id.use_in_products == True):
                if attr_data.attr_id.id == magento_attr.openerp_id.id:
                    for value_id in attr_data.value_ids:
                        value_bind = value_id.magento_binding_ids.filtered(
                            lambda rec: rec.magento_id and rec.backend_id.id == magento_attr.backend_id.id
                        )

                        if value_bind:
                            res[magento_attr.magento_code].append(value_bind.magento_id)

                    break

        return res


class ConfigurableProductExportMapper(Component):
    _name = 'magento.product.configurable.export.mapper'
    _inherit = 'magento.export.mapper'
    #_apply_on = ['magento.template.product']
    _apply_on = ['magento.product.template']

    direct = [
        ('name', 'name'),
        ('base_default_code', 'sku'),
        #('description_sale', 'description'),
        ('description', 'short_description'),
        ('list_price', 'price'),
    ]

    @mapping
    def add_description(self, record):
        description = record.description
        if record.is_spare_part:
            description = "<h2>"+str(record.name)+"</h2><p><br></p><h3>Ausführung:</h3><ul class='decorate-list'>"
            for property in record.shopware_property_ids:
                if property.attribute_id.id != 878:  # Added related to OD-941
                    description += "<li>"+str(property.attribute_id.name)+": "+str(", ".join([val.name for val in property.value_ids]))+"</li>"
            description += "</ul>"
        return {'description_sale': description}

    @only_create
    @mapping
    def websites(self, record):
        website_ids = []
        # binder = self.binder_for('magento.website')
        for website in self.backend_record.website_ids:
            # website_id = binder.to_backend(website.id)
            website_ids.append(website.magento_id)
        return {'websites': website_ids}

    @only_create
    @mapping
    def product_type(self, record):
        return {
            'type_id': CONFIGURABLE_PRODUCT
        }

    @changed_by('attribute_set_id')
    @mapping
    def set(self, record):
        res = {}
        if record.magento_attribute_set_id:
            res['set'] = record.magento_attribute_set_id.magento_id
        return res

    @only_create
    @mapping
    def categories(self, record):
        category_ids = []

        if record.magento_category_id and record.magento_category_id.magento_id:
            category_ids.append(int(record.magento_category_id.magento_id))
        elif self.backend_record.default_product_ctg_id:
            category_ids.append(int(self.backend_record.default_product_ctg_id))

        if len(category_ids) == 0:
            raise Warning(_('Product category is not properly set!'))

        return {'categories': category_ids}

    @changed_by('active')
    @mapping
    def status(self, record):
        if record.active:
            return {'status': 1}
        return {'status': 2}

    @only_create
    @mapping
    def system_attributes(self, record):
        to_skip = ['status', 'visibility']

        res = {
            # 'tax_class_id': DEFAULT_TAX_CLASS_ID,
        }

        for system_attr_val in self.backend_record.product_system_val_ids:
            attribute = system_attr_val.magento_attribute_id
            attribute_val = system_attr_val.magento_attr_value_id

            if not (attribute.magento_code and attribute_val.magento_id) or attribute.magento_code in to_skip:
                continue

            res[attribute.magento_code] = attribute_val.magento_id

        return res

    @changed_by('attribute_data_ids')
    @mapping
    def additional_attributes(self, record):
        res = {}
        return res  # Commented as suggestions from Tobias.

        if not record.attribute_data_ids:
            return {}

        magento_attribute_set = record.magento_attribute_set_id

        for magento_attr in magento_attribute_set.magento_attribute_ids.filtered(
                lambda rec: rec.use_in_products == True and rec.type in (SELECT_TYPE, CONFIGURABLE_TYPE)):

            if not magento_attr.magento_id or magento_attr.magento_code == 'visibility':
                continue

            found = False

            for attr_data in record.attribute_data_ids.filtered(lambda rec: rec.attr_id.use_in_products == True):
                if attr_data.attr_id.id == magento_attr.openerp_id.id:
                    value_bind = attr_data.value_id.magento_binding_ids.filtered(
                        lambda rec: rec.magento_id and rec.backend_id.id == magento_attr.backend_id.id
                    )

                    if value_bind:
                        found = True
                        res[magento_attr.magento_code] = value_bind.magento_id

                    break

            if not found:
                res[magento_attr.magento_code] = 0

        return res

    @changed_by('textual_attribute_data_ids')
    @mapping
    def additional_textual_attributes(self, record):
        res = {}
        return res  # Commented as suggestions from Tobias.

        if not record.textual_attribute_data_ids:
            return {}

        magento_attribute_set = record.magento_attribute_set_id

        for magento_attr in magento_attribute_set.magento_attribute_ids.filtered(
                lambda rec: rec.use_in_products == True and rec.type in (TEXT_TYPE, SIMPLE_TEXT_TYPE)):

            if not magento_attr.magento_id:
                continue

            found = False

            for attr_data in record.textual_attribute_data_ids.filtered(
                    lambda rec: rec.attr_id.use_in_products == True):
                if attr_data.attr_id.id == magento_attr.openerp_id.id:
                    if attr_data.value_id:
                        found = True
                        res[magento_attr.magento_code] = attr_data.value_id

                    break

            if not found:
                res[magento_attr.magento_code] = ''

        return res


class ProductExporter(Component):
    _name = 'magento.product.product.exporter'
    _inherit = 'magento.exporter'
    _apply_on = ['magento.product.product']
    _usage = 'record.exporter'

    def __init__(self, connector_env):
        super(ProductExporter, self).__init__(connector_env)
        self.storeview_id = None
        self.link_to_parent = False
        self.fields = None

    def _should_import(self):
        return False

    def run(self, binding_id, *args, **kwargs):
        self.fields = kwargs.get('fields', {})
        res = super(ProductExporter, self).run(binding_id, *args, **kwargs)

        # Grimm Patch adding start
        if type(self.env['magento.product.product']) == type(binding_id):
            enable_qty_increments = 1 if binding_id.openerp_id.is_package else 0
            use_config_enable_qty_increments = 0 if binding_id.openerp_id.is_package else 1
            use_config_qty_increments = 0 if binding_id.openerp_id.is_package else 1
            pack_qty = binding_id.openerp_id.package_id.qty_no if binding_id.openerp_id.package_id else 1
            if binding_id.magento_id:
                data_dict = {'use_config_enable_qty_increments': use_config_enable_qty_increments,
                             'use_config_qty_increments': use_config_qty_increments,
                             'enable_qty_increments': enable_qty_increments,
                             'qty_increments': pack_qty}
                self.backend_adapter.update_inventory(binding_id.magento_id, data_dict)
        #Grimm Patch end
        return res

    def _should_trigger_translations_export(self, product_binding):
        if not self.backend_record.synch_product_translations:
            return False

        allowed_fields = self.env['product.template'].get_storeview_specific_fields()
        updated_fields = list(self.fields.keys()) if self.fields else allowed_fields

        allowed_fields = set(allowed_fields)
        updated_fields = set(updated_fields)

        res = len(list(allowed_fields.intersection(updated_fields))) > 0
        return res

    def _after_export(self):
        pass
        binding = self.binding

        # if self._should_trigger_translations_export(binding):
        #     export_storeview_translations.delay(self.session, binding._name,
        #                                         binding.id, fields=self.fields, priority=7)

        # TODO fix me
        # if self.link_to_parent:
        #     link_variant_to_configurable.delay(self.session, binding._name, binding.id, priority=7)

        # image_exporter = self.component(usage='product.image.exporter')
        for magento_img in binding.magento_image_ids:
            if magento_img.magento_id:
                continue
            magento_img.with_delay().export_record()


class ConfigurableProductExporter(Component):
    _name = 'magento.product.template.exporter'
    _inherit = 'magento.exporter'
    _apply_on = ['magento.product.template']
    _usage = 'record.exporter'

    # _base_mapper_usage = 'magento.product.configurable.export.mapper'

    def __init__(self, connector_env):
        super(ConfigurableProductExporter, self).__init__(connector_env)
        self.storeview_id = None
        self.fields = None

    def _should_import(self):
        return False

    def _update(self, data):
        assert self.magento_id
        self._validate_update_data(data)
        self.backend_adapter.write(int(self.magento_id), data, storeview_id=self.storeview_id)

    def run(self, binding_id, *args, **kwargs):
        self.fields = kwargs.get('fields', {})
        res = super(ConfigurableProductExporter, self).run(binding_id, *args, **kwargs)
        return res

    def _should_trigger_variants_batch_export(self):
        if not self.fields:
            return True

        fields = set(self.fields.keys())
        config_only_fields = self.env['product.template'].get_config_only_fields_to_export()
        config_only_fields = set(config_only_fields)
        res = fields != config_only_fields
        return res

    def _should_trigger_variant_export(self, product_binding):
        return True

    def _should_trigger_translations_export(self, product_binding):
        if not self.backend_record.synch_product_translations:
            return False

        allowed_fields = self.env['product.template'].get_storeview_specific_fields()
        updated_fields = list(self.fields.keys()) if self.fields else allowed_fields

        allowed_fields = set(allowed_fields)
        updated_fields = set(updated_fields)

        res = len(list(allowed_fields.intersection(updated_fields))) > 0
        return res

    def _after_export(self):
        ptmpl_binding = self.binding

        # TODO fix me
        # if self._should_trigger_translations_export(ptmpl_binding):
        #     export_storeview_translations.delay(self.session, ptmpl_binding._name,
        #                                         ptmpl_binding.id, fields=self.fields, priority=7)
        #
        # if self._should_trigger_variants_batch_export():
        #     for pp_bind in ptmpl_binding.magento_product_variant_ids:
        #         if self._should_trigger_variant_export(pp_bind):
        #             link_to_parent = True if not pp_bind.magento_id else False
        #             export_product.delay(self.session, pp_bind._name, pp_bind.id, link_to_parent=link_to_parent,
        #                                  fields=self.fields)

        for magento_img in ptmpl_binding.magento_image_ids:
            if magento_img.magento_id:
                continue
            magento_img.with_delay().export_record()


# class VariantToConfigurableLinker(MagentoBaseExporter):
#     _model_name = 'magento.product.product'
#
#     def link_variant_to_config(self, magento_configurable_id, magento_simple_id, attributes={}):
#         return self.backend_adapter.link_variant_to_configurable_product(
#             magento_configurable_id, magento_simple_id, attributes=attributes
#         )
#
#     def run(self, binding_id):
#         self.binding_id = binding_id
#         self.binding_record = self._get_openerp_data()
#         attributes_data = self.mapper.attributes(self.binding_record)
#         config_binding = self.binding_record.magento_product_tmpl_id
#         assert config_binding and config_binding.magento_id
#         self.link_variant_to_config(config_binding.magento_id, self.binding_record.magento_id,
#                                     attributes=attributes_data)


def valid_export_fields(vals_dict, fields):
    if not vals_dict:
        return True

    updated_fields = set(vals_dict)
    fields = set(fields)
    res_fields = list(updated_fields.intersection(fields))
    res = len(res_fields) > 0
    return res


class MagentoProductListener(Component):
    _name = 'magento.binding.product.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['magento.product.product', 'magento.product.template']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        return True # magento_stop
        if record.backend_id.products_sync_type == PRODUCTS_ODOO_MASTER:
            link_parent = False
            if record._name == 'magento.product.product' and record.magento_product_tmpl_id and \
                    record.magento_product_tmpl_id.magento_id:
                link_parent = True
            record.with_delay().export_record()


class MagentoProductProductListener(Component):
    _name = 'magento.product.product.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['product.product']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        return True # magento_stop
        allowed_fields = self.env['product.template'].get_pp_fields_to_export()
        if not valid_export_fields(fields, allowed_fields):
            return False
        for pp_bind in record.magento_bind_ids:
            if pp_bind.backend_id.products_sync_type != PRODUCTS_ODOO_MASTER or not pp_bind.magento_id:
                continue
            pp_bind.with_delay().export_record(fields=fields)


class MagentoProductTemplateListener(Component):
    _name = 'magento.product.template.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['product.template']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        return True # magento_stop
        allowed_fields = self.env['product.template'].get_ptmpl_fields_to_export()
        if not valid_export_fields(fields, allowed_fields):
            return False

        if record.magento_type == CONFIGURABLE_PRODUCT:
            bindings_collection = record.magento_ptmpl_bind_ids
        else:
            # bindings_collection = record.product_variant_ids and record.product_variant_ids[0].magento_bind_ids
            bindings_collection = record.magento_pp_bind_ids

        for binding in bindings_collection:
            if binding.backend_id.products_sync_type != PRODUCTS_ODOO_MASTER or not binding.magento_id:
                continue
            binding.with_delay().export_record(fields=fields)

# @on_record_create(model_names=['magento.product.template', 'magento.product.product'])
# def product_export_delay(session, model_name, record_id, vals):
#     if session.context.get('connector_no_export', False):
#         return False
#
#     record = session.env[model_name].browse(record_id)
#     if record.backend_id.products_sync_type == PRODUCTS_ODOO_MASTER:
#         link_parent = False
#         if model_name == 'magento.product.product' and record.magento_product_tmpl_id and \
#                 record.magento_product_tmpl_id.magento_id:
#             link_parent = True
#
#         export_product.delay(session, model_name, record.id, link_to_parent=link_parent, fields=None)


# @on_record_write(model_names=['product.template'])
# def ptmpl_update_delay(session, model_name, record_id, vals):
#     if session.context.get('connector_no_export', False):
#         return False
#
#     allowed_fields = session.env['product.template'].get_ptmpl_fields_to_export()
#     if not valid_export_fields(vals, allowed_fields):
#         return False
#
#     record = session.env[model_name].browse(record_id)
#     bindings_collection = None
#
#     if record.magento_type == CONFIGURABLE_PRODUCT:
#         bindings_collection = record.magento_ptmpl_bind_ids
#     else:
#         # bindings_collection = record.product_variant_ids and record.product_variant_ids[0].magento_bind_ids
#         bindings_collection = record.magento_pp_bind_ids
#
#     for binding in bindings_collection:
#         if binding.backend_id.products_sync_type != PRODUCTS_ODOO_MASTER or not binding.magento_id:
#             continue
#
#         export_product.delay(session, binding._name, binding.id, link_to_parent=False, fields=vals)
#
#
# @on_record_write(model_names=['product.product'])
# def product_update_delay(session, model_name, record_id, vals):
#     if session.context.get('connector_no_export', False):
#         return False
#
#     allowed_fields = session.env['product.template'].get_pp_fields_to_export()
#     if not valid_export_fields(vals, allowed_fields):
#         return False
#
#     record = session.env[model_name].browse(record_id)
#     for pp_bind in record.magento_bind_ids:
#         if pp_bind.backend_id.products_sync_type != PRODUCTS_ODOO_MASTER or not pp_bind.magento_id:
#             continue
#
#         export_product.delay(session, pp_bind._name, pp_bind.id, link_to_parent=False, fields=vals)
#
#
# @job(default_channel='root.magento')
# def export_product(session, model_name, binding_id, link_to_parent=False, fields=None):
#     """ Export product to Magento"""
#
#     record = session.env[model_name].browse(binding_id)
#
#     env = get_environment(session, model_name, record.backend_id.id)
#     exporter = env.get_connector_unit(MagentoExporter)
#     exporter.link_to_parent = link_to_parent
#     res = exporter.run(binding_id, fields=fields)
#     return res
#
#
# @job(default_channel='root.magento')
# def link_variant_to_configurable(session, model_name, binding_id):
#     """ Assign variant to configurable product """
#
#     record = session.env[model_name].browse(binding_id)
#     env = get_environment(session, model_name, record.backend_id.id)
#     linker = env.get_connector_unit(VariantToConfigurableLinker)
#     res = linker.run(binding_id)
#     return res
#
#
# def _get_openerp_data(self):
#     """ Return the raw OpenERP data for ``self.binding_id`` """
#     record = self.model.browse(self.binding_id)
#     if record.backend_id.default_lang_id:
#         record = record.with_context(lang=record.backend_id.default_lang_id.code)
#     return record


# MagentoBaseExporter._get_openerp_data = _get_openerp_data
