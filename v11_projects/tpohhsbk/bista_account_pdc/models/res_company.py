# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    pdc_type = fields.Selection([('automatic', 'Automatic'),
                                 ('manual', 'Manual')], string='PDC Type',
                                default='automatic')
