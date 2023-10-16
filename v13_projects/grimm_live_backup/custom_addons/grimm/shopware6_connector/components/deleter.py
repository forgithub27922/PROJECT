# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.tools.translate import _
from odoo.addons.component.core import AbstractComponent


class Shopware6Deleter(AbstractComponent):
    """ Base deleter for Shopware """
    _name = 'shopware6.exporter.deleter'
    _inherit = 'base.deleter'
    _usage = 'record.exporter.deleter'

    def run(self, shopware6_id):
        """ Run the synchronization, delete the record on Shopware

        :param shopware6_id: identifier of the record to delete
        """
        deleted = self.backend_adapter.delete(shopware6_id)
        msg_string = _('Record %s deleted on Shopware6') % (shopware6_id,)
        if deleted == 404:
            msg_string = _('Record %s does not exist or already deleted on Shopware6.)') % (shopware6_id,)
        return msg_string
