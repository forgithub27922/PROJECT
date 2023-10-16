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
    _name = 'hr.gratuity'
    _inherit = ['mail.thread']
    _description = 'Gratuity'

    name = fields.Char('Description', required=True,
                       track_visibility='onchange')
    create_date = fields.Date('Create Date', default=fields.Date.context_today)
    resignation_contract_ids = fields.One2many('gratuity.resignation',
                                               'gratuity_id',
                                               string='Resignation Gratuity')
    termination_contract_ids = fields.One2many('gratuity.termination',
                                               'gratuity_id',
                                               string='Termination Gratuity')
    country_id = fields.Many2one('res.country', 'Nationality')
    date = fields.Date('Date')
    notes = fields.Text('Comments')
    company_id = fields.Many2one('res.company', string='Company',
                                 required=True,
                                 default=lambda self: self.env.user.company_id)
    user_id = fields.Many2one('res.users', string='User',
                              default=lambda self: self.env.user)

    @api.one
    @api.constrains('resignation_contract_ids')
    def check_resignation_contract(self):
        previous_to_exp = 0.0
        for resign_rec in self.resignation_contract_ids:
            if previous_to_exp \
                    and previous_to_exp != resign_rec.from_experience:
                wrn_msg = 'Resignation: Experience line can not be ovelapped.'
                raise ValidationError(_(wrn_msg))
            if not any([resign_rec.from_experience, resign_rec.to_experience]):
                wrn_msg = 'Resignation: From and to experience can not be ' \
                          'same.'
                raise ValidationError(_(wrn_msg))
            previous_to_exp = resign_rec.to_experience

    @api.one
    @api.constrains('termination_contract_ids')
    def check_termination_contract(self):
        previous_to_exp = 0.0
        for terminate_rec in self.termination_contract_ids:
            if previous_to_exp \
                    and previous_to_exp != terminate_rec.from_experience:
                wrn_msg = 'Termination: Experience line can not be ovelapped.'
                raise ValidationError(_(wrn_msg))
            if not any([terminate_rec.from_experience,
                        terminate_rec.to_experience]):
                wrn_msg = 'Termination: From and to experience can not ' \
                          'be same.'
                raise ValidationError(_(wrn_msg))
            previous_to_exp = terminate_rec.to_experience

    @api.one
    @api.constrains('company_id')
    def check_termination_contract(self):
        self._cr.execute('''SELECT company_id FROM hr_gratuity
                            GROUP BY company_id
                            HAVING count(company_id) > 1''')
        data = [gratuity[0] for gratuity in self._cr.fetchall()]
        if data:
            wrn_msg = 'Can not configure Gratuity more than one for ' \
                      'same company.'
            raise ValidationError(_(wrn_msg))


class GratuityResignation(models.Model):
    _name = 'gratuity.resignation'
    _description = 'Gratuity Contract Resignation'
    _order = "from_experience"

    from_experience = fields.Float('From Experience', required=True)
    to_experience = fields.Float('To Experience', required=True)
    eosb = fields.Float('EOSB')
    days = fields.Integer('Days')
    allowed_gratuity_days = fields.Float('Allowed Gratuity Days')
    gratuity_id = fields.Many2one('hr.gratuity', 'Resignation Gratuity ID',
                                  ondelete='cascade')
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)

    @api.constrains('allowed_gratuity_days')
    def check_allowed_gratuity(self):
        for each in self:
            if each.allowed_gratuity_days < 0:
                raise ValidationError(
                    "You can't enter negative allowed gratuity days.")


class GratuityTermination(models.Model):
    _name = 'gratuity.termination'
    _description = 'Gratuity Contract Termination'
    _order = "from_experience"

    from_experience = fields.Float('From Experience', required=True)
    to_experience = fields.Float('To Experience', required=True)
    eosb = fields.Float('EOSB')
    days = fields.Integer('Days')
    allowed_gratuity_days = fields.Float('Allowed Gratuity Days')
    gratuity_id = fields.Many2one('hr.gratuity', 'Termination Gratuity ID',
                                  ondelete='cascade')
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)

    @api.constrains('allowed_gratuity_days')
    def check_allowed_gratuity(self):
        for each in self:
            if each.allowed_gratuity_days < 0:
                raise ValidationError(
                    "You can't enter negative allowed gratuity days.")
