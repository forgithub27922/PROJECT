# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pdc_type = fields.Selection([('automatic', 'Automatic'),
                                 ('manual', 'Manual')],
                                related='company_id.pdc_type',
                                string='PDC Type',
                                default='automatic')
