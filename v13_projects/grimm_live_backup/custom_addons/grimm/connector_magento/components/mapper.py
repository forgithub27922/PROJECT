# -*- coding: utf-8 -*-
# © 2013 Guewen Baconnier,Camptocamp SA,Akretion
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import AbstractComponent
from odoo.addons.connector.components.mapper import mapping
from datetime import datetime

class MagentoImportMapper(AbstractComponent):
    _name = 'magento.import.mapper'
    _inherit = ['base.magento.connector', 'base.import.mapper']
    _usage = 'import.mapper'

    @mapping
    def mapping_date(self, record):
        fmt = '%Y-%m-%dT%H:%M:%S'
        res = {}
        if record.get('created_at', False) and record.get('created_at').find("T") >= 0:
            res["created_at"] = str(datetime.strptime(record.get('created_at').split('+')[0], fmt))
        if record.get('updated_at', False) and record.get('updated_at').find("T") >= 0:
            res["updated_at"] = str(datetime.strptime(record.get('updated_at').split('+')[0], fmt))
        return res


class MagentoExportMapper(AbstractComponent):
    _name = 'magento.export.mapper'
    _inherit = ['base.magento.connector', 'base.export.mapper']
    _usage = 'export.mapper'

    def map_record(self, record, parent=None):
        """ Inherited method to export data based on backend configuration language.

        :param record: record to transform
        :param parent: optional parent record, for items

        """
        backend_id = getattr(record, "backend_id", False)
        if backend_id:
            lang = backend_id.default_lang_id
            if lang.code:
                record = record.with_context(lang=lang.code)

        return super(MagentoExportMapper, self).map_record(record, parent)


def normalize_datetime(field):
    """Change a invalid date which comes from Magento, if
    no real date is set to null for correct import to
    OpenERP"""

    def modifier(self, record, to_attr):
        if record.get(field, '') == '0000-00-00 00:00:00':
            return None
        return record.get(field)
    return modifier
