# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class HrGratuity(models.Model):
    _inherit = 'hr.gratuity'

    nationality_ids = fields.One2many('gratuity.nationality',
                                      'gratuity_id',
                                      string='Locality')
    other_nationality_ids = fields.One2many('gratuity.other.nationality',
                                            'gratuity_id',
                                            string='Expats')

    @api.one
    @api.constrains('nationality_ids')
    def check_nationality(self):
        previous_to_exp = 0.0
        for nation_rec in self.nationality_ids:
            if previous_to_exp \
                    and previous_to_exp != nation_rec.from_experience:
                wrn_msg = 'Nationality: Experience line can not be ovelapped.'
                raise ValidationError(_(wrn_msg))
            if not any([nation_rec.from_experience, nation_rec.to_experience]):
                wrn_msg = 'Nationality: From and to experience can not be ' \
                          'same.'
                raise ValidationError(_(wrn_msg))
            previous_to_exp = nation_rec.to_experience

    @api.one
    @api.constrains('other_nationality_ids')
    def check_other_nationality(self):
        previous_to_exp = 0.0
        for other_nation_rec in self.other_nationality_ids:
            if previous_to_exp \
                    and previous_to_exp != other_nation_rec.from_experience:
                wrn_msg = 'Other Nationality: Experience line can not be ' \
                          'ovelapped.'
                raise ValidationError(_(wrn_msg))
            if not any([other_nation_rec.from_experience,
                        other_nation_rec.to_experience]):
                wrn_msg = 'Other Nationality: From and to experience can ' \
                          'not be same.'
                raise ValidationError(_(wrn_msg))
            previous_to_exp = other_nation_rec.to_experience


class GratuityNationality(models.Model):
    _name = 'gratuity.nationality'
    _description = 'Gratuity Nationality'
    _order = "from_experience"

    from_experience = fields.Float('From Experience', required=True)
    to_experience = fields.Float('To Experience', required=True)
    eosb = fields.Float('Applicable')
    days = fields.Integer('Days')
    allowed_gratuity_days = fields.Float('Allowed Gratuity Days')
    gratuity_id = fields.Many2one('hr.gratuity',
                                  'Nationality Gratuity',
                                  ondelete='cascade')
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)

    @api.constrains('allowed_gratuity_days')
    def check_allowed_gratuity(self):
        for each in self:
            if each.allowed_gratuity_days < 0:
                raise ValidationError(
                    "You can't enter negative allowed gratuity days.")


class GratuityOtherNationality(models.Model):
    _name = 'gratuity.other.nationality'
    _description = 'Gratuity Other Nationality'
    _order = "from_experience"

    from_experience = fields.Float('From Experience', required=True)
    to_experience = fields.Float('To Experience', required=True)
    eosb = fields.Float('Applicable')
    days = fields.Integer('Days')
    allowed_gratuity_days = fields.Float('Allowed Gratuity Days')
    gratuity_id = fields.Many2one('hr.gratuity',
                                  'Other Nationality Gratuity',
                                  ondelete='cascade')
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)

    @api.constrains('allowed_gratuity_days')
    def check_allowed_gratuity(self):
        for each in self:
            if each.allowed_gratuity_days < 0:
                raise ValidationError(
                    "You can't enter negative allowed gratuity days.")
