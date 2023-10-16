# -*- coding: utf-8 -*-
##############################################################################
#
# Skyscend Business Soluitions
# Copyright (C) 2019  (http://www.skyscendbs.com)
#
# Skyscend Business Soluitions Pvt. Ltd.
# Copyright (C) 2020  (http://www.skyscendbs.com)
##############################################################################
from odoo import api, fields, models, _


class sh_message_wizard(models.TransientModel):
    _name = "sh.message.wizard"
    
    def get_default(self):
        if self.env.context.get("message", False):
            return self.env.context.get("message")
        return False 

    name = fields.Text(string="Message", readonly=True, default=get_default)

