# -*- coding: utf-8 -*-

from odoo.addons.component.core import Component
from odoo.addons.connector_magento.components.importer import TranslationImporter


class OpenfellasTranslationImporter(Component):
    _name = 'magento.translation.importer'
    _inherit = 'magento.translation.importer'
    _apply_on = TranslationImporter._apply_on + [
        'magento.product.attribute.set',
        'magento.product.attribute',
        'magento.product.attribute.value',
        'magento.product.template'
    ]
    _usage = 'translation.importer'

    magento_data_per_storeview = {}

    def _manual_data_models(self):
        res = ['magento.product.attribute.value']
        return res

    def _get_magento_data(self, storeview_id=None):
        if storeview_id is None:
            storeview_id = -1

        storeview_id_key = storeview_id

        if self.model._name in self._manual_data_models():
            if self.magento_data_per_storeview.get(storeview_id_key, False):
                return self.magento_data_per_storeview[storeview_id_key]
            return {}

        res = super(OpenfellasTranslationImporter, self)._get_magento_data(storeview_id=storeview_id)
        # self.magento_data_per_storeview[storeview_id_key] = res
        return res

    def _get_invalid_translation_data(self, data):
        res = []

        for k in list(data.keys()):
            if type(data[k]) in (str, str):
                data[k] = data[k].strip()

            if not data[k]:
                res.append(k)

        return res

    def _get_translatable_fields(self, binding_id):
        if self.model._name == 'magento.product.product':
            binding = self.model.browse(binding_id)
            if binding.magento_product_tmpl_id:
                return self.env['product.product'].get_child_product_translatable_fields()

        fields = self.model.fields_get()
        translatable_fields = [field for field, attrs in fields.items()
                               if attrs.get('translate')]

        return translatable_fields

    def run(self, magento_id, binding_id, mapper_class=None):
        self.magento_id = magento_id

        storeviews = self.env['magento.storeview'].search(
            [('backend_id', '=', self.backend_record.id)]
        )
        default_lang = self.backend_record.default_lang_id
        lang_storeviews = [sv for sv in storeviews
                           if sv.lang_id and sv.lang_id != default_lang]
        if not lang_storeviews:
            return

        # find the translatable fields of the model
        translatable_fields = self._get_translatable_fields(binding_id)

        if mapper_class is None:
            mapper = self.mapper
        else:
            mapper = self.unit_for(mapper_class)

        binding = self.model.browse(binding_id)
        lang_codes = []

        for storeview in lang_storeviews:
            if storeview.lang_id.code in lang_codes:
                continue

            lang_codes.append(storeview.lang_id.code)

            lang_record = self._get_magento_data(storeview.magento_id)
            map_record = mapper.map_record(lang_record)
            record = map_record.values(current_storeview_id=storeview.magento_id)

            data = dict((field, value) for field, value in record.items()
                        if field in translatable_fields)

            invalid_keys = self._get_invalid_translation_data(data)
            for k in invalid_keys:
                data.pop(k, None)

            if data:
                binding.with_context(connector_no_export=True, lang=storeview.lang_id.code).write(data)
