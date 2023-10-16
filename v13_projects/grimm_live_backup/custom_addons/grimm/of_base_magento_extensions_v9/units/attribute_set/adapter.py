# -*- coding: utf-8 -*-

from odoo.addons.component.core import Component


class ProductAttributeSetAdapter(Component):
    _name = 'magento.product.attribute.set.adapter'
    _inherit = 'magento.adapter'
    _apply_on = 'magento.product.attribute.set'
    _magento_model = 'product_attribute_set'

    def create(self, data):
        set_name = data['name']
        skeleton_set_id = data['skeleton_set_id']
        res = self._call('%s.create' % (self._magento_model), [set_name, skeleton_set_id])
        return res

    def write(self, id, data):
        return True

    def search(self, filters=None):
        return [int(row['set_id']) for row in
                self._call('%s.list' % self._magento_model, [filters] if filters else [{}])]

    def assign_attribute_to_set(self, attribute_magento_id, attrset_magento_id):
        assert attribute_magento_id and attrset_magento_id
        res = self._call('%s.attributeAdd' % (self._magento_model), [attribute_magento_id, attrset_magento_id])
        return res

    def remove_attribute_from_set(self, attribute_magento_id, attrset_magento_id):
        assert attribute_magento_id and attrset_magento_id
        res = self._call('%s.attributeRemove' % (self._magento_model,), [attribute_magento_id, attrset_magento_id])
        return res

    def read(self, id, attributes=None):
        set_id = int(id)
        sets = self._call('%s.list' % self._magento_model, [{}]) or []
        for attr_set in sets:
            if int(attr_set['set_id']) == set_id:
                return attr_set
        return False
