# -*- coding: utf-8 -*-

# Copyright (C) 2019 Skyscend Business Solutions (<http://skyscendbs.com>)
# Copyright (C) 2020 Skyscend Business Solutions  Pvt. Ltd.(<http://skyscendbs.com>)

from odoo import fields, models, api, _

class Partner(models.Model):
    _inherit = 'res.partner'

    is_customer = fields.Boolean("Is Customer?")

    @api.model
    def create_from_ui(self, partner):
        print("partner::::::::::", partner, dir(partner))
        partner.update({'is_customer': True})
        return super(Partner, self).create_from_ui(partner)
