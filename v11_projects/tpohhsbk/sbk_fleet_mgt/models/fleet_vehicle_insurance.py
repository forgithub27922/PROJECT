# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################
from odoo import api, fields, models,_
from odoo.exceptions import ValidationError


class fleet_vehicle_insurance(models.Model):
    _name = 'fleet.vehicle.insurance'
    _rec_name = 'vehicle_id'

    vehicle_id = fields.Many2one('fleet.vehicle.model',string="Vehicle")
    country_id = fields.Many2one('res.country', string="Country")
    res_state_id = fields.Many2one('res.country.state', string='Emirate')
    insurance_start_date = fields.Date(string="Start Date")
    insurance_end_date = fields.Date(string="End Date")
    # state = fields.Selection([('register','Registration'),('expired','Expired')],string="State",default="register")
    vehicle_insurance_document_ids = fields.One2many('fleet.vehicle.document','vehicle_insurance_id',string="Vehicle Document")
    notes = fields.Text(string="Notes")
    company_id = fields.Many2one('res.company',string="Company",default=lambda self:self.env.user.company_id.id)
    insurance_document_count = fields.Integer(string="Count",compute='count_insurance_vehicle_document')

    @api.constrains('insurance_start_date','insurance_end_date')
    def check_date_range(self):
        for insurance in self:
            if insurance.insurance_end_date < insurance.insurance_start_date:
                raise ValidationError(_('Please enter proper date range.'))

    @api.multi
    def count_insurance_vehicle_document(self):
        for vehicle_insurance in self:
            vehicle_insurance.insurance_document_count = len(vehicle_insurance.vehicle_insurance_document_ids)

    @api.multi
    def show_insurance_document(self):
        return {
            'name': 'Insurance Document',
            'type': 'ir.actions.act_window',
            'res_model': 'fleet.vehicle.document',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'domain':[('id','in',self.vehicle_insurance_document_ids.ids)],
            'context':{'default_vehicle_insurance_id':self.id}
        }