# -*- coding: utf-8 -*-
from odoo.addons.component.core import Component


class ProductAttributeAdapter(Component):
    _name = 'magento.product.attribute.adapter'
    _inherit = 'magento.adapter'
    _apply_on = 'magento.product.attribute'
    _magento_model = 'product_attribute'

    def get_options(self, attribute_magento_id, storeview_id=None):
        res = self._call('ol_catalog_product_attribute.options', [attribute_magento_id, storeview_id])
        return res

    def assign_option_to_attribute(self, attribute_magento_id, option_data):
        value_magento_id = None
        res = self._call('product_attribute.addOption', [attribute_magento_id, option_data])

        if res:
            option_name = option_data['label'][0]['value']
            options = self._call('catalog_product_attribute.options', [attribute_magento_id, None])

            for opt in options:
                if opt['label'] == option_name:
                    value_magento_id = opt['value']
                    break

        return value_magento_id

    def remove_option_from_attribute(self, attribute_magento_id, option_magento_value):
        res = self._call('product_attribute.removeOption', [attribute_magento_id, option_magento_value])
        return res

    def create(self, data):
        res = self._call('%s.create' % (self._magento_model), [data])
        return res

    def search(self, magento_set_id):
        res = self._call('%s.list' % self._magento_model, [magento_set_id])
        res = [int(row['attribute_id']) for row in res]
        return res

    def _adjust_attribute_data(self, attribute_data={}):
        attribute_id = int(attribute_data['attribute_id'])
        if self.backend_record.attrs_default_storeview_id:
            options_list = self.get_options(attribute_id,
                                            storeview_id=self.backend_record.attrs_default_storeview_id.magento_id)

            attribute_data['options'] = options_list
        options_list = attribute_data.get('options', [])
        options_res = []

        for magento_option in options_list:
            if magento_option.get('value', False) and magento_option.get('label', False):
                magento_option['attribute_id'] = attribute_id
                options_res.append(magento_option)

        attribute_data['options'] = options_res

    def read(self, id, attributes=None):
        res = super(ProductAttributeAdapter, self).read(id, attributes)
        self._adjust_attribute_data(res)
        return res

class ProductAttributeValueAdapter(Component):
    _name = 'magento.product.attribute.value.adapter'
    _inherit = 'magento.adapter'
    _apply_on = 'magento.product.attribute.value'
    _magento_model = 'catalog_product_attribute'

    def create(self, data):
        #res = self._call('%s.create' % (self._magento_model), [data])
        print("Create product attribute value Adapter is called.... with data  ===>",data)
        #return res

    def unlink(self, data):
        #res = self._call('%s.create' % (self._magento_model), [data])
        print("unlink product attribute value Adapter is called.... with data  ===>",data)
        #return res

    '''
    def search(self, magento_set_id):
        res = self._call('%s.list' % self._magento_model, [magento_set_id])
        res = [int(row['attribute_id']) for row in res]
        return res

    def _adjust_attribute_data(self, attribute_data={}):
        attribute_id = int(attribute_data['attribute_id'])
        if self.backend_record.attrs_default_storeview_id:
            options_list = self.get_options(attribute_id,
                                            storeview_id=self.backend_record.attrs_default_storeview_id.magento_id)

            attribute_data['options'] = options_list
        options_list = attribute_data.get('options', [])
        options_res = []

        for magento_option in options_list:
            if magento_option.get('value', False) and magento_option.get('label', False):
                magento_option['attribute_id'] = attribute_id
                options_res.append(magento_option)

        attribute_data['options'] = options_res

    def read(self, id, attributes=None):
        res = super(ProductAttributeAdapter, self).read(id, attributes)
        self._adjust_attribute_data(res)
        return res
    '''
