# -*- coding: utf-8 -*-

from openerp import models, fields


class User(models.Model):
    _inherit = 'res.users'

    dashboard_image = fields.Binary("Dashboard Background", attachment=True, help="Set custom dashboard background image." )
