# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.tools.translate import _
from odoo.addons.component.core import AbstractComponent


class MagentoDeleter(AbstractComponent):
    """ Base deleter for Magento """
    _name = 'magento.exporter.deleter'
    _inherit = 'base.deleter'
    _usage = 'record.exporter.deleter'

    def run(self, magento_id):
        """ Run the synchronization, delete the record on Magento

        :param magento_id: identifier of the record to delete
        """
        self.backend_adapter.delete(magento_id)
        return _('Record %s deleted on Magento') % (magento_id,)
