# -*- coding: utf-8 -*-

from openerp import models, fields, api


class MailTemplate(models.Model):
    _inherit = 'mail.template'

    not_overwrite = fields.Boolean(string='Not overwrite', help='Existed contents not overwrite', default=False)
