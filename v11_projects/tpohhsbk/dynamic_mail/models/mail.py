# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################


from odoo import api, fields, models, _

class MailMail(models.Model):
    _inherit = "mail.mail"

    dynamic_config_id = fields.Many2one('dynamic.mail',string='Dynamic Config',copy=False)
