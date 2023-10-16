# -*- coding: utf-8 -*-

from odoo.addons.component.core import Component


class CatalogImageAdapter(Component):
    _name = 'magento.product.image.adapter'
    _inherit = 'magento.adapter'
    _apply_on = 'magento.product.image'
    _magento_model = 'catalog_product_attribute_media'

    def read(self, id, image_name, storeview_id=None):
        return self._call('%s.info' % (self._magento_model), [int(id), image_name, storeview_id, 'id'])

    def create(self, product_id, data, storeview_id=None):
        return self._call('%s.create' % self._magento_model, [int(product_id), data, storeview_id, 'id'])

    def write(self, product_id, id, data, storeview_id=None):
        return self._call('%s.update' % self._magento_model,
                          [int(product_id), id, data, storeview_id, 'id'])

    def delete(self, product_id, id):
        return self._call('%s.remove' % self._magento_model, [int(product_id), id, 'id'])
