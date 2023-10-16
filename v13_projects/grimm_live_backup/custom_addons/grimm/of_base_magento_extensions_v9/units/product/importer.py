# -*- coding: utf-8 -*-


import logging

from odoo import _
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping, only_create
from odoo.addons.connector_magento.models.product.importer import ProductImportMapper
from html2text import HTML2Text
from ..translation.importer import OpenfellasTranslationImporter
from ...constants import (CONFIGURABLE_PRODUCT, SIMPLE_PRODUCT, NO_IMAGES_SYNC, SELECT_TYPE, CONFIGURABLE_TYPE, \
                          TEXT_TYPE, SIMPLE_TEXT_TYPE)

_logger = logging.getLogger(__name__)

# Variables for testing purposes
PRODUCTS_IMPORT_LIMIT = 0
START_IMPORT_INDEX = 23
END_IMPORT_INDEX = 28


def _shrink_product_ids(product_ids):
    if PRODUCTS_IMPORT_LIMIT == 0:
        return product_ids

    if START_IMPORT_INDEX == END_IMPORT_INDEX:
        return product_ids

    res = product_ids[START_IMPORT_INDEX:END_IMPORT_INDEX]
    return res


class ConfigurableProductImportMapper(Component):
    _name = 'magento.product.template.mapper'
    _inherit = 'magento.import.mapper'
    _apply_on = 'magento.product.template'

    new_mappings = []

    remove_mappings = [
        ('type_id', 'product_type'),
        ('sku', 'default_code')
    ]

    direct = list(set(ProductImportMapper.direct).union(set(new_mappings)) - set(remove_mappings))

    @only_create
    @mapping
    def categories(self, record):
        result = {}
        mag_categories = record['categories']
        binder = self.binder_for('magento.product.category')

        categories = []
        main_categ = self.backend_record.default_category_id
        arbitrary_categ = main_categ.magento_bind_ids.filtered(lambda rec: rec.backend_id.id == self.backend_record.id)
        if arbitrary_categ:
            arbitrary_categ = arbitrary_categ[0]

        for mag_category_id in mag_categories:
            cat_rec = binder.to_openerp(mag_category_id, browse=True)
            categories.append(cat_rec)

        for ctg in categories:
            if not ctg:
                continue

            main_categ = ctg.openerp_id
            arbitrary_categ = ctg

        if not main_categ:
            raise Exception(
                _('No categories could be found in odoo for following magento category ids: %s. '
                  'You must either map manually/import those categories, or set default category on Magento Backend!' % (
                      mag_categories))
            )

        result['categ_id'] = main_categ.id
        result['arbitrary_magento_ctg_id'] = arbitrary_categ.id

        return result

    @mapping
    def is_active(self, record):
        active = record['status'] == '1'
        return {
            'active': active
        }

    @mapping
    def configurable_data(self, record):
        return {
            'magento_type': CONFIGURABLE_PRODUCT,
            'has_variants': True,
        }

    @mapping
    def price_configuration(self, record):
        return {
            'price_calculation': 'variant_independent'
        }

    @mapping
    def type(self, record):
        return {'type': 'product'}

    @mapping
    def base_default_code(self, record):
        magento_sku = record.get('sku', '')

        return {
            'base_default_code': magento_sku
        }

    @mapping
    def attribute_set(self, record):
        magento_set_id = record.get('set', False)

        if magento_set_id:
            binder = self.binder_for('magento.product.attribute.set')
            attr_set_id = binder.to_openerp(int(magento_set_id), unwrap=True)

            return {
                'attribute_set_id': attr_set_id
            }

        return {}


class VariantProductImportMapper(Component):
    _name = 'magento.product.variant.import.mapper'
    _inherit = 'magento.import.mapper'
    _apply_on = ['magento.product.product']

    direct = [
        ('type_id', 'product_type'),
        ('sku', 'default_code'),
        ('ean', 'barcode')
    ]

    @mapping
    def product_tmpl_id(self, record):

        parent_id = record.get('parent_id', False)

        if parent_id:
            binder = self.binder_for('magento.product.template')
            tmpl_id = binder.to_openerp(parent_id, unwrap=True)
            return {
                'product_tmpl_id': tmpl_id
            }

        return {}

    @mapping
    def lst_price(self, record):
        res = {}
        res['lst_price'] = record.get('price', 0.0)
        return res

    def _map_fields_from_parent(self):
        res = ['magento_type', 'has_variants', 'price_calculation', 'list_price', 'type']
        return res

    @mapping
    def configurable_parent_fields(self, record):
        res = {}
        ptmpl_data = self.product_tmpl_id(record)
        if not ptmpl_data:
            return {}

        ptmpl_id = ptmpl_data['product_tmpl_id']
        ptmpl = self.env['product.template'].browse(ptmpl_id)
        parent_fields = self._map_fields_from_parent()

        for field_name in parent_fields:
            res[field_name] = ptmpl[field_name]

        return res

    @mapping
    def attribute_values(self, record):

        if record.get('set', False):

            value_ids = []

            binder = self.binder_for('magento.product.attribute.set')
            magento_attr_set = binder.to_openerp(int(record['set']), browse=True)

            if not magento_attr_set:
                raise Exception('You must import all attribute sets!')

            for magento_attribute in magento_attr_set.magento_attribute_ids:
                if magento_attribute.is_configurable and magento_attribute.magento_code in list(record.keys()) and \
                        record[magento_attribute.magento_code]:
                    found_value = False

                    for magento_attr_value in magento_attribute.magento_attribute_value_ids:

                        if record[magento_attribute.magento_code] == magento_attr_value.magento_id:
                            value_ids.append(magento_attr_value.openerp_id.id)
                            found_value = True
                            break

                    if not found_value:
                        pass

            res = [(6, 0, value_ids)]

            return {
                'product_template_attribute_value_ids': res #Odoo13Change
            }

        return {}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


class OpenfellasProductImportMapper(Component):
    _name = 'magento.product.product.import.mapper'
    _inherit = 'magento.product.product.import.mapper'
    _apply_on = ['magento.product.product']

    new_mappings = [
        ('ean', 'barcode'),
    ]

    remove_mappings = []

    direct = list(set(ProductImportMapper.direct).union(set(new_mappings)) - set(remove_mappings))

    @mapping
    def attribute_set(self, record):
        magento_set_id = record.get('set', False)

        if magento_set_id:
            binder = self.binder_for('magento.product.attribute.set')
            attr_set_id = binder.to_openerp(int(magento_set_id), unwrap=True)

            return {
                'attribute_set_id': attr_set_id
            }

        return {}

    @only_create
    @mapping
    def categories(self, record):
        result = {}
        mag_categories = record['categories']
        binder = self.binder_for('magento.product.category')

        categories = []
        main_categ = self.backend_record.default_category_id
        arbitrary_categ = main_categ.magento_bind_ids.filtered(lambda rec: rec.backend_id.id == self.backend_record.id)
        if arbitrary_categ:
            arbitrary_categ = arbitrary_categ[0]

        for mag_category_id in mag_categories:
            cat_rec = binder.to_openerp(mag_category_id, browse=True)
            categories.append(cat_rec)

        for ctg in categories:
            if not ctg:
                continue

            main_categ = ctg.openerp_id
            arbitrary_categ = ctg

        if not main_categ:
            raise Exception(
                _('No categories could be found in odoo for following magento category ids: %s. '
                  'You must either map manually/import those categories, or set default category on Magento Backend!' % (
                      mag_categories))
            )

        result['categ_id'] = main_categ.id
        result['arbitrary_magento_ctg_id'] = arbitrary_categ.id

        return result


class OpenfellasProductImporter(Component):
    _name = 'magento.product.product.importer'
    _inherit = 'magento.product.product.importer'
    _apply_on = ['magento.product.product']

    def __init__(self, connector_env):
        super(OpenfellasProductImporter, self).__init__(connector_env)
        self.parent_product_id = None
        self.import_history_id = None
        self.initial_variant_import = False

    @property
    def mapper(self):
        if self._mapper is None:
            mapper_class = OpenfellasProductImportMapper
            if self.parent_product_id:
                mapper_class = VariantProductImportMapper

            self._mapper = self.unit_for(mapper_class)

        return self._mapper

    def _import_dependencies(self):
        record = self.magento_record

        if not self.parent_product_id:
            if self.backend_record.import_categories:
                for mag_category_id in record['categories']:
                    self._import_dependency(mag_category_id, 'magento.product.category')

            if record['type_id'] == 'bundle':
                self._import_bundle_dependencies()

    def _must_skip(self):
        res = super(OpenfellasProductImporter, self)._must_skip()

        if self.parent_product_id and not self.initial_variant_import:
            history = self.env['products.import.history'].browse(self.import_history_id)
            if history.exists_in_history('variant', self.magento_id):
                if not res: res = ''
                res += _('Variant product already imported with configurable product')

        return res

    def _resolve_parent_product(self, magento_id):
        if self.parent_product_id:
            return

        binding = self.binder.to_openerp(magento_id, browse=True)
        if binding and binding.magento_product_tmpl_id:
            self.parent_product_id = binding.magento_product_tmpl_id.magento_id

    def _get_magento_data(self):
        res = super(OpenfellasProductImporter, self)._get_magento_data()
        res['parent_id'] = self.parent_product_id
        return res

    def _update_attribute_lines(self, binding):
        res = True
        lines_to_update = []
        attrs_to_add = {}

        for value in binding.product_template_attribute_value_ids: #Odoo13Change
            attr_exists = False

            for line in binding.attribute_line_ids:

                if line.attribute_id.id == value.attribute_id.id:
                    attr_exists = True

                    if value.id not in line.value_ids.ids:
                        lines_to_update.append((1, line.id, {'value_ids': [(4, value.id)]}))

                    break

            if not attr_exists:
                if not attrs_to_add.get(value.attribute_id.id, False):
                    attrs_to_add[value.attribute_id.id] = []

                attrs_to_add[value.attribute_id.id].append(value.id)

        for attr_id in list(attrs_to_add.keys()):
            lines_to_update.append((0, 0, {'attribute_id': attr_id, 'value_ids': [(6, 0, attrs_to_add[attr_id])]}))

        if len(lines_to_update) > 0:
            binding = binding.with_context(create_product_variant=True, connector_no_export=True)
            res = binding.write({'attribute_line_ids': lines_to_update})

        return res

    def run(self, magento_id, force=False):
        self._resolve_parent_product(magento_id)
        res = super(OpenfellasProductImporter, self).run(magento_id, force=force)
        return res

    def _adjust_textual_content(self, text, attr_code=None):
        if not text:
            return ''

        text_parser = HTML2Text()
        text_parser.ignore_links = True
        text_parser.ignore_emphasis = True
        res = text_parser.handle(text)
        return res

    def _adjust_attributes(self, binding, attribute_type):
        magento_record = self.magento_record
        backend_id = self.backend_record.id
        attr_codes = list(magento_record.keys())
        update_vals = []

        field_attr_type_mapps = {
            SELECT_TYPE: 'attribute_data_ids',
            TEXT_TYPE: 'textual_attribute_data_ids',
            SIMPLE_TEXT_TYPE: 'textual_attribute_data_ids'
        }

        attrs_prod_collection_field = field_attr_type_mapps[attribute_type]
        attributes_on_prod_collection = binding[attrs_prod_collection_field]

        attributes_to_consider = self.env['magento.product.attribute'].search(
            [('magento_code', 'in', attr_codes), ('backend_id', '=', self.backend_record.id),
             ('use_in_products', '=', True), ('magento_id', '!=', False), ('type', '=', attribute_type)]
        )

        for attr_data in attributes_on_prod_collection:
            attr_bind = attr_data.attr_id.magento_binding_ids.filtered(lambda rec: rec.backend_id.id == backend_id)
            if attr_bind and (attr_bind.magento_code not in attr_codes or not attr_bind.use_in_products):
                update_vals.append((2, attr_data.id))

        for attr_bind in attributes_to_consider:
            existing = attributes_on_prod_collection.filtered(lambda rec: rec.attr_id.id == attr_bind.openerp_id.id)
            value_id = None

            if attr_bind.type in (SELECT_TYPE, CONFIGURABLE_TYPE):
                value_bind = attr_bind.magento_attribute_value_ids.filtered(
                    lambda rec: rec.magento_id == magento_record[attr_bind.magento_code]
                )

                value_id = value_bind and value_bind.openerp_id.id or False

            elif attr_bind.type in (TEXT_TYPE, SIMPLE_TEXT_TYPE):
                value_id = magento_record[attr_bind.magento_code]
                value_id = self._adjust_textual_content(value_id)

            if existing:
                if value_id:
                    update_vals.append((1, existing.id, {'attr_id': attr_bind.openerp_id.id, 'value_id': value_id}))
                else:
                    update_vals.append((2, existing.id))

            elif value_id:
                update_vals.append((0, 0, {'attr_id': attr_bind.openerp_id.id, 'value_id': value_id}))

        if update_vals:
            binding.with_context(connector_no_export=True).write({attrs_prod_collection_field: update_vals})

        return True

    def _adjust_additional_attributes(self, binding):
        for attribute_type in (SELECT_TYPE, TEXT_TYPE, SIMPLE_TEXT_TYPE):
            self._adjust_attributes(binding, attribute_type)

        return True

    def _after_import(self, binding):
        translation_mapper_class = ProductImportMapper

        if self.parent_product_id:
            self._update_attribute_lines(binding)
            translation_mapper_class = VariantProductImportMapper
        else:
            self._adjust_additional_attributes(binding)

            if self.magento_record['type_id'] == 'bundle':
                bundle_importer = self.component(usage='product.bundle.importer',
                                                 model_name='magento.product.product')
                bundle_importer.run(binding.id, self.magento_record)

        if self.backend_record.product_images_import_type != NO_IMAGES_SYNC:
            image_importer = self.component(usage='product.image.importer',
                                            model_name='magento.product.product')
            image_importer.run(self.magento_id, binding.id)

        if self.backend_record.synch_product_translations:
            translation_importer = self.component(usage='translation.importer',
                                                  model_name='magento.product.product')
            translation_importer.run(self.magento_id, binding.id, mapper_class=translation_mapper_class)


class ConfigurableProductImporter(Component):
    _name = 'magento.product.template.importer'
    _inherit = 'magento.importer'
    _apply_on = ['magento.product.template']

    # _base_mapper = ConfigurableProductImportMapper

    def __init__(self, connector_env):
        super(ConfigurableProductImporter, self).__init__(connector_env)
        self.parent_product_id = None
        self.import_history_id = None

    @property
    def model(self):
        return self.connector_env.model.with_context(create_product_product=False)

    def _update(self, binding, data):
        binding = binding.with_context(create_product_product=False, create_product_variant=True)
        return super(ConfigurableProductImporter, self)._update(binding, data)

    def _import_dependencies(self):
        record = self.magento_record

        if self.backend_record.import_categories:
            for mag_category_id in record['categories']:
                self._import_dependency(mag_category_id, 'magento.product.category')

    def _must_skip(self):
        return False

    def _validate_product_type(self, data):
        return True

    def write_import_history(self, field_name, product_id):
        history_rec = self.env['products.import.history'].browse(self.import_history_id)
        res = history_rec.update_history(field_name, product_id)
        return res

    def _should_import_variant(self, variant_magento_id):
        if self.backend_record.force_import_of_variants:
            return True

        res = not self.binder_for('magento.product.product').to_openerp(external_id=variant_magento_id)
        return res

    def _adjust_textual_content(self, text, attr_code=None):
        if not text:
            return ''

        text_parser = HTML2Text()
        text_parser.ignore_links = True
        text_parser.ignore_emphasis = True
        res = text_parser.handle(text)
        return res

    def _adjust_attributes(self, binding, attribute_type):
        magento_record = self.magento_record
        backend_id = self.backend_record.id
        attr_codes = list(magento_record.keys())
        update_vals = []

        field_attr_type_mapps = {
            SELECT_TYPE: 'attribute_data_ids',
            TEXT_TYPE: 'textual_attribute_data_ids',
            SIMPLE_TEXT_TYPE: 'textual_attribute_data_ids',
        }

        attrs_prod_collection_field = field_attr_type_mapps[attribute_type]
        attributes_on_prod_collection = binding[attrs_prod_collection_field]

        attributes_to_consider = self.env['magento.product.attribute'].search(
            [('magento_code', 'in', attr_codes), ('backend_id', '=', self.backend_record.id),
             ('use_in_products', '=', True), ('magento_id', '!=', False), ('type', '=', attribute_type)]
        )

        for attr_data in attributes_on_prod_collection:
            attr_bind = attr_data.attr_id.magento_binding_ids.filtered(lambda rec: rec.backend_id.id == backend_id)
            if attr_bind and (attr_bind.magento_code not in attr_codes or not attr_bind.use_in_products):
                update_vals.append((2, attr_data.id))

        for attr_bind in attributes_to_consider:
            existing = attributes_on_prod_collection.filtered(lambda rec: rec.attr_id.id == attr_bind.openerp_id.id)
            value_id = None

            if attr_bind.type in (SELECT_TYPE, CONFIGURABLE_TYPE):
                value_bind = attr_bind.magento_attribute_value_ids.filtered(
                    lambda rec: rec.magento_id == magento_record[attr_bind.magento_code]
                )

                value_id = value_bind and value_bind.openerp_id.id or False

            elif attr_bind.type in (TEXT_TYPE, SIMPLE_TEXT_TYPE):
                value_id = magento_record[attr_bind.magento_code]
                value_id = self._adjust_textual_content(value_id)

            if existing:
                if value_id:
                    update_vals.append((1, existing.id, {'attr_id': attr_bind.openerp_id.id, 'value_id': value_id}))
                else:
                    update_vals.append((2, existing.id))

            elif value_id:
                update_vals.append((0, 0, {'attr_id': attr_bind.openerp_id.id, 'value_id': value_id}))

        if update_vals:
            binding.with_context(connector_no_export=True).write({attrs_prod_collection_field: update_vals})

        return True

    def _adjust_additional_attributes(self, binding):
        for attribute_type in (SELECT_TYPE, TEXT_TYPE, SIMPLE_TEXT_TYPE):
            self._adjust_attributes(binding, attribute_type)

        return True

    def _after_import(self, binding):
        super(ConfigurableProductImporter, self)._after_import(binding)
        self._adjust_additional_attributes(binding)

        # if int(self.magento_id)==25983:
        #     raise Exception('Test configurable product import fail!')

        if self.backend_record.synch_product_translations:
            translation_importer = self.unit_for(TranslationImporter)
            translation_importer.run(self.magento_id, binding.id, mapper_class=ConfigurableProductImportMapper)

        if self.backend_record.product_images_import_type != NO_IMAGES_SYNC:
            image_importer = self.component(usage='product.image.importer',
                                            model_name='magento.product.product')
            image_importer.run(self.magento_id, binding.id)

        magento_variants_data = self.backend_adapter.get_variants_of_configurable(binding.magento_id)
        found_variant_ids = [-1, -2]

        for variant in magento_variants_data:
            found_variant_ids.append(variant['product_id'])

            if self._should_import_variant(variant['product_id']):
                self.write_import_history('variant', variant['product_id'])
                initial_import_variant_product.delay(
                    self.session, 'magento.product.product',
                    self.backend_record.id,
                    variant['product_id'],
                    variant['parent_id'],
                    self.import_history_id,
                    priority=5
                )

        found_variant_ids = tuple(found_variant_ids)

        deactivate_products_sql = """
                                  UPDATE product_product
                                  SET active=FALSE
                                  WHERE product_tmpl_id=%s AND id IN (
                                          SELECT openerp_id
                                          FROM magento_product_product
                                          WHERE magento_product_tmpl_id=%s AND (magento_id IS NULL OR magento_id::INT NOT IN %s)
                                  );
                                  """ % (binding.openerp_id.id, binding.id, found_variant_ids)

        remove_bindings_sql = """
                              DELETE FROM magento_product_product
                              WHERE magento_product_tmpl_id=%s AND (magento_id IS NULL OR magento_id::INT NOT IN %s);
                              """ % (binding.id, found_variant_ids)

        self.env.cr.execute(deactivate_products_sql)
        self.env.cr.execute(remove_bindings_sql)

        return True


@openfellas_magento_extensions
class ConfigurableProductBatchImporter(DelayedBatchImporter):
    _model_name = ['magento.product.template']

    def __init__(self, connector_env):
        super(ConfigurableProductBatchImporter, self).__init__(connector_env)
        self.import_history_id = None

    def write_import_history(self, field_name, product_id):
        history_rec = self.env['products.import.history'].browse(self.import_history_id)
        res = history_rec.update_history(field_name, product_id)
        return res

    def _import_record(self, record_id, **kwargs):
        """ Delay the import of the records"""
        self.write_import_history('configurable', record_id)
        import_configurable_product.delay(
            self.session,
            self.model._name,
            self.backend_record.id,
            record_id,
            self.import_history_id,
            priority=5,
            **kwargs
        )

    def run(self, filters=None):
        """ Run the synchronization """

        filters['type'] = ['=', CONFIGURABLE_PRODUCT]
        from_date = filters.pop('from_date', None)
        to_date = filters.pop('to_date', None)
        record_ids = self.backend_adapter.search(filters,
                                                 from_date=from_date,
                                                 to_date=to_date)

        record_ids = _shrink_product_ids(record_ids)

        _logger.info('search for magento products %s returned %s', filters, record_ids)
        for record_id in record_ids:
            self._import_record(record_id)


@openfellas_magento_extensions
class OpenfellasProductBatchImporter(ProductBatchImporter):
    _model_name = ['magento.product.product']

    def __init__(self, connector_env):
        super(OpenfellasProductBatchImporter, self).__init__(connector_env)
        self.import_history_id = None
        self.product_types = [SIMPLE_PRODUCT]

    def _import_record(self, record_id, **kwargs):
        """ Delay the import of the records"""
        import_product.delay(
            self.session,
            self.model._name,
            self.backend_record.id,
            record_id,
            self.import_history_id,
            **kwargs
        )

    def get_product_ids_to_import(self, magento_record_ids):
        import_history = self.env['products.import.history'].browse(self.import_history_id)
        imported_variant_ids = import_history.get_list_of_ids('variant')
        magento_ids = set(magento_record_ids)
        variant_ids = set(imported_variant_ids)
        res = list(magento_ids - variant_ids)
        return res

    def _check_history(self):
        assert self.import_history_id

        history = self.env['products.import.history'].browse(self.import_history_id)
        failed_configs = history.get_list_of_ids('configurable_failed')
        if failed_configs:
            raise Exception(
                'Some of configurable products have failed to import. First you must resolve those imports, '
                'otherwise parent-child structure for simple products might not be imported correctly!')

    def run(self, filters=None):
        """ Run the synchronization """
        assert len(self.product_types) > 0, 'YOu must specify product types to import'

        self._check_history()

        if filters is None:
            filters = {}

        filters['type'] = ['in', self.product_types]

        from_date = filters.pop('from_date', None)
        to_date = filters.pop('to_date', None)
        record_ids = self.backend_adapter.search(filters,
                                                 from_date=from_date,
                                                 to_date=to_date)

        products_ids_to_import = self.get_product_ids_to_import(record_ids)
        products_ids_to_import = _shrink_product_ids(products_ids_to_import)

        _logger.info('search for magento products %s returned %s', filters, products_ids_to_import)

        products_count = len(products_ids_to_import)
        counter = 0
        for record_id in products_ids_to_import:
            counter += 1
            _logger.info('[%s/%s] Preparing import for product id=%s' % (counter, products_count, record_id))
            self._import_record(record_id)


@job(default_channel='root.magento')
def import_configurable_product(session, model_name, backend_id, magento_id, import_history_id, force=True):
    """ Import configurable product from Magento """

    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(ConfigurableProductImporter)

    try:
        importer.import_history_id = import_history_id
        importer.run(magento_id, force=force)
        history = session.env['products.import.history'].browse(import_history_id)
        history.check_and_remove_from_history('configurable_failed', magento_id)

    except Exception as ex:
        with transaction(session.env.cr.dbname) as cr1:
            new_env = Environment(cr1, session.uid, session.context)
            new_session = ConnectorSession.from_env(new_env)
            history = new_session.env['products.import.history'].browse(import_history_id)
            history.update_history('configurable_failed', magento_id)

        raise ex


@job(default_channel='root.magento')
def initial_import_variant_product(session, model_name, backend_id, magento_id, magento_parent_id, import_history_id,
                                   force=True):
    """ Import variant product from Magento """

    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(OpenfellasProductImporter)
    magento_id = int(magento_id)
    importer.parent_product_id = int(magento_parent_id)
    importer.import_history_id = import_history_id
    importer.initial_variant_import = True
    importer.run(magento_id, force=force)


@job(default_channel='root.magento')
def import_product(session, model_name, backend_id, magento_id, import_history_id, force=True):
    """ Import product from Magento """

    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(OpenfellasProductImporter)
    importer.import_history_id = import_history_id
    importer.run(magento_id, force=force)


@job(default_channel='root.magento')
def product_import_batch(session, model_name, backend_id, import_history_id, filters=None):
    """ Prepare a batch import of products from Magento """

    env = get_environment(session, model_name, backend_id)
    importer = env.get_connector_unit(DelayedBatchImporter)
    importer.import_history_id = import_history_id
    importer.run(filters=filters)
