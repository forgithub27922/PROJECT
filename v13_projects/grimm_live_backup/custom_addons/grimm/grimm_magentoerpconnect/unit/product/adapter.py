# -*- coding: utf-8 -*-


from odoo.addons.component.core import Component
from odoo.addons.connector_magento.components.backend_adapter import MAGENTO_DATETIME_FORMAT


class GrimmConfigurableProductAdapter(Component):
    _name = 'magento.product.template.adapter'
    _inherit = 'magento.product.template.adapter'
    _apply_on = 'magento.product.template'
    _magento_model = 'ol_catalog_product'

    def search(self, filters=None, from_date=None, to_date=None):
        if filters is None:
            filters = {}

        if filters.get('search_created_only', False):
            filters.pop('search_created_only', None)

        res = super(GrimmConfigurableProductAdapter, self).search(filters=filters, from_date=from_date, to_date=to_date)
        return res

    def search_existing(self, filters=None, from_date=None, to_date=None):
        res = self.search(filters=filters, from_date=from_date, to_date=to_date)

        existing_ids = []
        binder = self.binder_for(self._model_name)

        for prod_id in res:
            if not binder.to_openerp(prod_id):
                continue
            existing_ids.append(prod_id)

        return existing_ids


class GrimmProductAdapter(Component):
    _name = 'magento.product.product.adapter'
    _inherit = 'magento.product.product.adapter'
    _apply_on = 'magento.product.product'
    _magento_model = 'ol_catalog_product'

    def search_new_products(self, filters=None, from_date=None, to_date=None):
        if filters is None:
            filters = {}
        dt_fmt = MAGENTO_DATETIME_FORMAT
        if from_date is not None:
            filters.setdefault('created_at', {})
            filters['created_at']['from'] = from_date.strftime(dt_fmt)
        if to_date is not None:
            filters.setdefault('created_at', {})
            filters['created_at']['to'] = to_date.strftime(dt_fmt)

        res = []
        binder = self.binder_for(self._model_name)

        for row in self._call('%s.list' % self._magento_model, [filters] if filters else [{}]):
            if binder.to_openerp(int(row['product_id'])):
                continue

            res.append(int(row['product_id']))

        return res

    def search_existing(self, filters=None, from_date=None, to_date=None):
        res = self.search(filters=filters, from_date=from_date, to_date=to_date)

        existing_ids = []
        binder = self.binder_for(self._model_name)

        for prod_id in res:
            if not binder.to_openerp(prod_id):
                continue

            existing_ids.append(prod_id)

        return existing_ids

    def search(self, filters=None, from_date=None, to_date=None):
        if filters is None:
            filters = {}

        if filters.get('search_created_only', False):
            filters.pop('search_created_only', None)
            res = self.search_new_products(filters=filters, from_date=from_date, to_date=to_date)
        else:
            res = super(GrimmProductAdapter, self).search(filters=filters, from_date=from_date, to_date=to_date)

        return res

    def search_product_link(self, p_type, product_id):
        results = self._call('catalog_product_link.list', [p_type, product_id, 'id'])
        #res = {int(row['product_id']): int(row['position']) for row in results}
        res = [int(row['product_id']) for row in results]
        return res

    def assign_product_link(self, p_type, product_id, linked_product_id, data={}):
        ret = self._call('catalog_product_link.assign', [p_type, product_id, linked_product_id, data, 'id'])
        return True if ret else False

    def remove_product_link(self, p_type, product_id, linked_product_id):
        ret = self._call('catalog_product_link.remove', [p_type, product_id, linked_product_id, 'id'])
        return True if ret else False
