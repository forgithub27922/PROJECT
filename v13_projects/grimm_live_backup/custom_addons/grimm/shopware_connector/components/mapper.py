# -*- coding: utf-8 -*-
# © 2013 Guewen Baconnier,Camptocamp SA,Akretion
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent


class ShopwareImportMapper(AbstractComponent):
    _name = 'shopware.import.mapper'
    _inherit = ['base.shopware.connector', 'base.import.mapper']
    _usage = 'import.mapper'


class ShopwareExportMapper(AbstractComponent):
    _name = 'shopware.export.mapper'
    _inherit = ['base.shopware.connector', 'base.export.mapper']
    _usage = 'export.mapper'

    def map_record(self, record, parent=None):
        """ Inherited method to export data based on backend configuration language.

        :param record: record to transform
        :param parent: optional parent record, for items

        """

        backend_id = getattr(record,"backend_id",False)
        if backend_id:
            lang = backend_id.default_lang_id
            if lang.code:
                record = record.with_context(lang=lang.code)

        return super(ShopwareExportMapper, self).map_record(record, parent)

def normalize_datetime(field):
    """Change a invalid date which comes from odoo, if
    no real date is set to null for correct import to
    OpenERP"""

    def modifier(self, record, to_attr):
        if record[field] == '0000-00-00 00:00:00':
            return None
        return record[field]
    return modifier
