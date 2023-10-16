# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright 2013 Camptocamp SA
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging
from odoo import models, fields, api, exceptions, _


MAX_POP_MESSAGES = 50

_logger = logging.getLogger(__name__)


class IrModelFields(models.Model):
    """ Ir Model Field added Boolean fields for trigger shopware update """
    _inherit = "ir.model.fields"
    update_shopware_trigger = fields.Boolean('On Update Shopware Trigger', help="Shopware Trigger will execute if user will update value of this field.", default=True)

    def change_update_trigger(self):
        '''
        Odoo not allowed to
        :return:
        '''
        for res in self:
            if res.update_shopware_trigger:
                self.env.cr.execute("update ir_model_fields set update_shopware_trigger='f' where id=%s;",(int(res.id),))
            else:
                self.env.cr.execute("update ir_model_fields set update_shopware_trigger='t' where id=%s;",(int(res.id),))