# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_address_validated = fields.Boolean(readonly=True, string='Is Validated?', default=False,
                                          help='Checks if the address is validated')

    def action_validate_address(self):
        try:
            addr = '%s, %s, %s, %s' % (self.street, self.zip, self.city, self.country_id.name)
            coordinates = self.env['base.geocoder']._call_openstreetmap(addr)
            if coordinates is None:
                raise UserError(_('Address may not be correct'))
            else:
                self.is_address_validated = True
        except IndexError:
            raise UserError(_('Address seems to be invalid!'))

        return {
            'effect': {
                'fadeout': 'slow',
                'message': _("Die angegebene Adresse ist gültig.!"),
                'type': 'rainbow_man',
            }
        }