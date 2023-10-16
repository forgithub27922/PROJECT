# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.tools.translate import _
from odoo.addons.component.core import AbstractComponent


class ShopwareDeleter(AbstractComponent):
    """ Base deleter for Shopware """
    _name = 'shopware.exporter.deleter'
    _inherit = 'base.deleter'
    _usage = 'record.exporter.deleter'

    def run(self, shopware_id):
        """ Run the synchronization, delete the record on Shopware

        :param shopware_id: identifier of the record to delete
        """
        self.backend_adapter.delete(shopware_id)
        return _('Record %s deleted on Shopware') % (shopware_id,)
