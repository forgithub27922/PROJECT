# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################
from odoo import api, fields, models, _


class fleet_vehicle(models.Model):
    _inherit = 'fleet.vehicle'

    country_id = fields.Many2one('res.country', string="Country")
    res_state_id = fields.Many2one('res.country.state', string="Emirate")
    vehicle_registration_count = fields.Integer(string="Registration Count", compute='count_vehicle_registration')
    vehicle_insurance_count = fields.Integer(string="Insurance Count", compute='count_vehicle_registration')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)

    @api.depends('model_id')
    def count_vehicle_registration(self):
        fleet_vehicle_registration_obj = self.env['fleet.vehicle.registration']
        fleet_vehicle_insurance_obj = self.env['fleet.vehicle.insurance']
        for each in self:
            registration_ids = fleet_vehicle_registration_obj.search([('vehicle_id', '=', each.model_id.id)])
            insurance_ids = fleet_vehicle_insurance_obj.search([('vehicle_id', '=', each.model_id.id)])
            each.vehicle_insurance_count = len(insurance_ids)
            each.vehicle_registration_count = len(registration_ids)

    @api.multi
    def do_open_vehicle_registration(self):
        action = self.env.ref('sbk_fleet_mgt.fleet_vehicle_registration_action').read()[0]
        registration_ids = self.env['fleet.vehicle.registration'].sudo(). \
            search([('vehicle_id', '=', self.model_id.id)])
        action['domain'] = [('id', 'in', registration_ids.ids)]
        action['context'] = {'default_vehicle_id': self.model_id.id,
                             'default_country_id': self.country_id.id,
                             'default_res_state_id': self.res_state_id.id}
        return action

    @api.multi
    def do_open_vehicle_insurance(self):
        action = self.env.ref('sbk_fleet_mgt.fleet_vehicle_insurance_action').read()[0]
        insurance_ids = self.env['fleet.vehicle.insurance'].sudo(). \
            search([('vehicle_id', '=', self.model_id.id)])
        action['domain'] = [('id', 'in', insurance_ids.ids)]
        action['context'] = {'default_vehicle_id': self.model_id.id,
                             'default_country_id': self.country_id.id,
                             'default_res_state_id': self.res_state_id.id}
        return action
