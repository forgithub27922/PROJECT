# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################
from odoo import api, fields, models,_
from odoo.exceptions import ValidationError


class fleet_vehicle_registration(models.Model):
    _name = 'fleet.vehicle.registration'
    _rec_name = 'vehicle_id'

    vehicle_id = fields.Many2one('fleet.vehicle.model',string="Vehicle")
    country_id = fields.Many2one('res.country', string="Country")
    res_state_id = fields.Many2one('res.country.state', string='Emirate')
    registration_start_date = fields.Date(string="Start Date")
    registration_end_date = fields.Date(string="End Date")
    owner_id = fields.Many2one('res.partner',string="Owner")
    # state = fields.Selection([('register','Registration'),('expired','Expired')],string="State",default="register")
    vehicle_registration_document_ids = fields.One2many('fleet.vehicle.document','vehicle_registration_id',string="Vehicle Document")
    notes = fields.Text(string="Notes")
    company_id = fields.Many2one('res.company',string="Company",default=lambda self:self.env.user.company_id.id)
    registration_document_count = fields.Integer(string="Count",compute='count_vehicle_document')

    @api.constrains('registration_start_date','registration_end_date')
    def check_date_range(self):
        for registration in self:
            if registration.registration_end_date < registration.registration_start_date:
                raise ValidationError(_('Please enter proper date range.'))

    @api.multi
    def count_vehicle_document(self):
        for vehicle_registration in self:
            vehicle_registration.registration_document_count = len(vehicle_registration.vehicle_registration_document_ids)

    @api.multi
    def show_registration_document(self):
        return {
            'name': 'Registration Document',
            'type': 'ir.actions.act_window',
            'res_model': 'fleet.vehicle.document',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'domain':[('id','in',self.vehicle_registration_document_ids.ids)],
            'context':{'default_vehicle_registration_id':self.id}
        }


class fleet_vehicle_document(models.Model):
    _name = 'fleet.vehicle.document'
    _description = 'Vehicle Document'

    name = fields.Char(string="Name")
    start_date = fields.Date(string="Start Date")
    expiry_date = fields.Date(string="Expiry Date")
    document_type_id = fields.Many2one('document.type',string="Document Type")
    type = fields.Selection([('Registration','Registration'),('Insurance','Insurance'),
                            ('Driver','Driver'),('Company','Company')],string="Type")
    partner_id = fields.Many2one('res.partner',string="Partner")
    vehicle_insurance_id = fields.Many2one('fleet.vehicle.insurance',string="Vehicle Insurance")
    vehicle_registration_id = fields.Many2one('fleet.vehicle.registration',string="Vehicle Registration")
    company_id = fields.Many2one('res.company',string="Company")
    ref_company_id = fields.Many2one('res.company',string="Company")
    vehicle_id = fields.Many2one('fleet.vehicle.model',string="Vehicle")

    @api.constrains('start_date','end_date')
    def check_date_range(self):
        for document in self:
            if document.expiry_date < document.start_date:
                raise ValidationError(_('Please enter proper date range.'))



