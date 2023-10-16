# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################
from odoo import api, fields, models,_


class res_partner(models.Model):
    _inherit = 'res.partner'

    driver = fields.Boolean(string="Is a Driver")
    driver_document_ids = fields.One2many('fleet.vehicle.document','partner_id',string="Driver Document")
    driver_document_count = fields.Integer(string="Count",compute='count_driver_document')

    @api.multi
    def count_driver_document(self):
        for driver_document in self:
            driver_document.driver_document_count = len(driver_document.driver_document_ids)

    @api.multi
    def show_driver_document(self):
        return {
            'name': 'Driver Document',
            'type': 'ir.actions.act_window',
            'res_model': 'fleet.vehicle.document',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'domain':[('id','in',self.driver_document_ids.ids)],
            'context':{'default_partner_id':self.id}
        }


class res_company(models.Model):
    _inherit = 'res.company'

    company_document_ids = fields.One2many('fleet.vehicle.document','ref_company_id',string="Company Document")
    company_document_count = fields.Integer(string="Count",compute='count_company_document')

    @api.multi
    def count_company_document(self):
        for company in self:
            company.company_document_count = len(company.company_document_ids)

    @api.multi
    def show_company_document(self):
        return {
            'name': 'Company Document',
            'type': 'ir.actions.act_window',
            'res_model': 'fleet.vehicle.document',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'domain':[('id','in',self.company_document_ids.ids)],
            'context':{'default_ref_company_id':self.id}
        }
