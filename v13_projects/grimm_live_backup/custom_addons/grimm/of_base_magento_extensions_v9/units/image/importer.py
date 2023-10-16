# -*- coding: utf-8 -*-


import base64
import logging
import urllib.error
import urllib.parse
import urllib.request

from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo.addons.connector_magento.models.product.importer import CatalogImageImporter

from ...constants import (CONFIGURABLE_PRODUCT, BASIC_IMAGES_SYNC, FULL_IMAGES_SYNC_ALL, FULL_IMAGES_SYNC_BASE, \
                          NO_IMAGES_SYNC)

_logger = logging.getLogger(__name__)


class OpenfellasCatalogImageImportPreparator(Component):
    _name = 'magento.product.image.importer'
    _inherit = 'magento.product.image.importer'
    _apply_on = CatalogImageImporter._apply_on + ['magento.product.template']

    def __init__(self, connector_env):
        super(OpenfellasCatalogImageImportPreparator, self).__init__(connector_env)
        self.magento_id = None
        self.mptmpl = None
        self.mpp = None

    def _get_image_field_name(self, binding):
        res = 'image'

        if self.model._name == 'magento.product.product':
            if binding.magento_product_tmpl_id:
                res = 'image_variant'

        return res

    def _resolve_product(self):
        assert self.magento_id
        magento_product_id = self.magento_id

        mptmpl = self.env['magento.product.template'].with_context(active_test=False).search(
            [('magento_id', '=', magento_product_id)]
        )

        self.mptmpl = mptmpl or None

        if not mptmpl:
            mpp = self.env['magento.product.product'].with_context(active_test=False).search(
                [('magento_id', '=', magento_product_id)]
            )

            self.mpp = mpp or None

    def _clear_existing_images(self, found_magento_images):
        img_magento_ids = ['-1', '-2']

        for img_data in found_magento_images:
            img_magento_ids.append(img_data['file'])

        img_magento_ids = tuple(img_magento_ids)

        where_clause = ''

        if self.mptmpl:
            where_clause = """product_tmpl_id=%s""" % (self.mptmpl.openerp_id.id)
        elif self.mpp:
            if self.mpp.magento_type == CONFIGURABLE_PRODUCT:
                where_clause = """variant_product_id=%s""" % (self.mpp.openerp_id.id)
            else:
                where_clause = """product_tmpl_id=%s""" % (self.mpp.product_tmpl_id.id)

        if where_clause:
            delete_query = """
                           DELETE FROM product_image
                           WHERE id in (
                                SELECT openerp_id
                                FROM magento_product_image
                                WHERE magento_id IS NULL OR magento_id NOT IN %s
                           ) AND %s;
                           """ % (img_magento_ids, where_clause)

            update_query = """
                    UPDATE product_image
                    SET is_base_image=FALSE, is_small_image=FALSE, is_thumbnail=FALSE
                    WHERE %s;
                    """ % (where_clause)

            self.env.cr.execute(delete_query)
            self.env.cr.execute(update_query)

    def run(self, magento_id, binding_id):
        self.magento_id = magento_id
        self._resolve_product()

        images = self._get_images()
        self._clear_existing_images(images)
        images = self._sort_images(images)

        if self.backend_record.product_images_import_type == BASIC_IMAGES_SYNC:
            binary = None
            while not binary and images:
                binary = self._get_binary_image(images.pop())
            if not binary:
                return
            model = self.model.with_context(connector_no_export=True, skip_image_update=True)
            binding = model.browse(binding_id)
            img_field_name = self._get_image_field_name(binding)

            binding.write({img_field_name: base64.b64encode(binary)})

        elif self.backend_record.product_images_import_type != NO_IMAGES_SYNC:
            images_collection = []

            if self.backend_record.product_images_import_type == FULL_IMAGES_SYNC_BASE:
                for img in images:
                    if 'image' in img.get('types', []):
                        images_collection.append(img)
                        break

            elif self.backend_record.product_images_import_type == FULL_IMAGES_SYNC_ALL:
                images_collection = images

            for img in images_collection:
                import_product_image.delay(
                    self.session, 'magento.product.image', self.backend_record.id, img['file'], self.magento_id
                )


class ProductImageImporter(Component):
    _name = 'magento.product.image.importer'
    _inherit = 'magento.importer'
    _apply_on = ['magento.product.image']
    _usage = 'record.importer'

    def __init__(self, connector_env):
        super(ProductImageImporter, self).__init__(connector_env)
        self.magento_product_id = None

    def _create(self, data):
        self._validate_data(data)
        model = self.model.with_context(connector_no_export=True, skip_bindings=True)
        binding = model.create(data)
        _logger.debug('%d created from magento %s', binding, self.magento_id)
        return binding

    def _get_magento_data(self):
        res = self.backend_adapter.read(self.magento_product_id, self.magento_id, None)
        res['magento_product_id'] = self.magento_product_id
        return res


class ProductImageImportMapper(Component):
    _name = 'magento.product.image.import.mapper'
    _inherit = 'magento.import.mapper'
    _apply_on = ['magento.product.image']

    def _get_binary_image(self, image_data):
        url = image_data['url'].encode('utf8')
        try:
            request = urllib.request.Request(url)
            if self.backend_record.auth_basic_username \
                    and self.backend_record.auth_basic_password:
                base64string = base64.b64encode(
                    '%s:%s' % (self.backend_record.auth_basic_username,
                               self.backend_record.auth_basic_password))
                request.add_header("Authorization", "Basic %s" % base64string)
            binary = urllib.request.urlopen(request)
        except urllib.error.HTTPError as err:
            if err.code == 404:
                # the image is just missing, we skip it
                raise Exception('Image %s not found!' % (url))
            else:
                # we don't know why we couldn't download the image
                # so we propagate the error, the import will fail
                # and we have to check why it couldn't be accessed
                raise
        else:
            return binary.read()

    @mapping
    def sequence(self, record):
        res = {}

        position = record.get('position')

        if position:
            res['sequence'] = int(position)

        return res

    @mapping
    def image_binary(self, record):
        res = {}

        binary_data = self._get_binary_image(record)

        b64_data = base64.b64encode(binary_data)
        image_types_data = self.image_types(record)

        if not image_types_data.get('is_standard', False):
            if binary_data:
                res['manual_image_data'] = b64_data

        elif binary_data:
            product_data = self.product_id(record)
            image_field = None
            product = None
            if product_data.get('product_tmpl_id', False):
                product = self.env['product.template'].browse(int(product_data['product_tmpl_id']))
                image_field = 'image'
            elif product_data.get('variant_product_id', False):
                product = self.env['product.product'].browse(int(product_data['variant_product_id']))
                image_field = 'image_variant'

            if product:
                product.with_context(skip_image_update=True).write({image_field: b64_data})

        return res

    @mapping
    def image_types(self, record):
        res = {}

        if record.get('types', False):
            types_mapp = {
                'image': {'is_base_image': True},
                'small_image': {'is_small_image': True},
                'thumbnail': {'is_thumbnail': True}
            }

            types = record['types']

            for t in types:
                if t in list(types_mapp.keys()):
                    res.update(types_mapp[t])

        if res.get('is_base_image', False):
            res['is_standard'] = True
        else:
            res['is_standard'] = False

        return res

    def _get_img_name(self, record, product):
        res = {}

        label = record.get('label', False)
        product_sku = product.base_default_code if product._name == 'magento.product.template' else product.default_code

        if not label:
            image_type_data = self.image_types(record)

            if image_type_data.get('is_standard', False):
                res['name'] = '%s Standard image' % (product_sku or '')
            else:
                res['name'] = 'No label-%s' % (record['file'] if record.get('file', False) else (product_sku or ''))
        else:
            res['name'] = label

        return res

    @mapping
    def product_id(self, record):
        res = {}

        magento_product_id = str(record['magento_product_id'])
        product = self.env['magento.product.template'].with_context(active_test=False).search(
            [('magento_id', '=', magento_product_id)]
        )

        if not product:
            product = self.env['magento.product.product'].with_context(active_test=False).search(
                [('magento_id', '=', magento_product_id)]
            )

        if product:
            if product._name == 'magento.product.template':
                res['product_tmpl_id'] = product.openerp_id.id
            elif product.magento_type != CONFIGURABLE_PRODUCT:
                res['product_tmpl_id'] = product.product_tmpl_id.id
            else:
                res['variant_product_id'] = product.openerp_id.id

        base_data = self._get_img_name(record, product)
        res.update(base_data)

        return res

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}



class CatalogImageBatchImport(Component):
    _name = 'magento.product.image.batch.importer'
    _inherit = 'magento.delayed.batch.importer'
    _apply_on = ['magento.product.image']

    def run(self, filters=None):
        # product_models = ['magento.product.product', 'magento.product.template']
        # binding_collections = []
        magento_ids = self.backend_adapter.search(filters,)
        # for model_name in product_models:
        #     res = self.env[model_name].search(
        #         [('backend_id', '=', self.backend_record.id), ('magento_id', '!=', False)])
        #     binding_collections.append(res)

        self._import_record(magento_ids)


# @job(default_channel='root.magento')
# def collect_product_images(session, model_name, backend_id, binding_id):
#     """Collect product images"""
#
#     env = get_environment(session, model_name, backend_id)
#     record = session.env[model_name].browse(binding_id)
#     importer = env.get_connector_unit(OpenfellasCatalogImageImportPreparator)
#     importer.run(int(record.magento_id), binding_id)



def import_product_image(session, model_name, backend_id, magento_img_id, magento_product_id):
    """ Import product image from Magento """
    pass
    # env = get_environment(session, model_name, backend_id)
    # img_importer = env.get_connector_unit(ProductImageImporter)
    # img_importer.magento_product_id = magento_product_id
    # img_importer.run(magento_img_id)
