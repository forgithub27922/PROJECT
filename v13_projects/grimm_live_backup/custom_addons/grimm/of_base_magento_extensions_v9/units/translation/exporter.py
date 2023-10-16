# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2016 Openfellas (http://openfellas.com) All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly advised to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################


from odoo.addons.component.core import Component


class TranslationExporter(Component):
    _name = 'magento.translation.exporter'
    _inherit = 'magento.exporter'
    _apply_on = [
        'magento.product.template',
        'magento.product.product',
    ]
    _usage = 'record.exporter'

    def __init__(self, working_context):
        super(TranslationExporter, self).__init__(working_context)
        self.magento_id = None
        self.binding_id = None
        self.binding_record = None

    def _get_invalid_translation_data(self, data):
        res = []

        for k in list(data.keys()):
            if type(data[k]) in (str, str):
                data[k] = data[k].strip()

            if not data[k]:
                res.append(k)

        return res

    def get_fields_to_export(self, binding):
        if binding._name in ('magento.product.template', 'magento.product.product'):
            return self.env['product.template'].get_storeview_specific_fields()
        return []

    def _export(self, binding_translated, fields, storeview):
        res = False
        map_record = self.mapper.map_record(binding_translated)
        record = map_record.values(fields=fields, current_storeview_id=storeview.magento_id)
        adapter = self.unit_for(GenericAdapter)

        if binding_translated._name in ('magento.product.template', 'magento.product.product'):
            res = adapter.write(int(binding_translated.magento_id), record, storeview_id=int(storeview.magento_id))

        return res

    def export_storeview_specific_values(self, storeview):
        if not storeview.lang_id:
            return False

        binding_lang = self.model.with_context(lang=storeview.lang_id.code).browse(self.binding_id)
        allowed_fields = self.get_fields_to_export(binding_lang)
        updated_fields = list(self.fields.keys()) if self.fields else allowed_fields

        allowed_fields = set(allowed_fields)
        updated_fields = set(updated_fields)

        fields_to_export = list(allowed_fields.intersection(updated_fields))

        if not fields_to_export:
            return False

        res = self._export(binding_lang, fields_to_export, storeview)
        return res

    def _resolve_mapper(self, binding_id):
        # Hook method to set some other mapper to the TranslationExporter object, instead of default one:
        # Example: self._mapper = self.unit_for(MapperClass)
        return

    def run(self, binding_id, fields=None):
        self._resolve_mapper(binding_id)
        self.binding_id = binding_id
        self.fields = fields or {}
        self.binding_record = self.model.browse(self.binding_id)
        self.magento_id = int(self.binding_record.magento_id)
        assert self.magento_id

        storeviews = self.env['magento.storeview'].search([('backend_id', '=', self.backend_record.id)])

        default_lang = self.backend_record.default_lang_id
        lang_storeviews = [sv for sv in storeviews if sv.lang_id and sv.lang_id != default_lang]

        if not lang_storeviews:
            return

        for storeview in lang_storeviews:
            self.export_storeview_specific_values(storeview)

        return True


@job(default_channel='root.magento')
def export_storeview_translations(session, model_name, binding_id, fields=None):
    """ Export storeview translations"""

    record = session.env[model_name].browse(binding_id)
    env = get_environment(session, model_name, record.backend_id.id)
    exporter = env.get_connector_unit(TranslationExporter)
    res = exporter.run(binding_id, fields=fields)
    return res
