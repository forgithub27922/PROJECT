# -*- coding: utf-8 -*-
# © 2013 Guewen Baconnier,Camptocamp SA,Akretion
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent
from odoo.addons.connector.components.mapper import mapping
import dateutil
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)


class ShopwareImportMapper(AbstractComponent):
    _name = 'shopware6.import.mapper'
    _inherit = ['base.shopware6.connector', 'base.import.mapper']
    _usage = 'import.mapper'

    @mapping
    def map_create_update_date(self, record):
        update_info = {}
        attr = record.get("data", {}).get("attributes", {})
        if attr:
            if attr.get('createdAt',False):
                #created_at = record.get('createdAt').split(".")[0].replace("T", " ")
                created_at = dateutil.parser.parse(attr.get('createdAt')).strftime('%Y-%m-%d %H:%M:%S')
                update_info["created_at"] = str(created_at)
            if attr.get('updatedAt', False):
                #updated_at = record.get('updatedAt').split(".")[0].replace("T", " ")
                updated_at = dateutil.parser.parse(attr.get('updatedAt')).strftime('%Y-%m-%d %H:%M:%S')
                update_info["updated_at"] = str(updated_at)
        return update_info

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}


class ShopwareExportMapper(AbstractComponent):
    _name = 'shopware6.export.mapper'
    _inherit = ['base.shopware6.connector', 'base.export.mapper']
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
