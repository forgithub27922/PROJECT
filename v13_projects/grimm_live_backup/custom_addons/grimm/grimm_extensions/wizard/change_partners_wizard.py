# -*- coding: utf-8 -*-

from odoo import models, api, fields, _
from odoo.exceptions import ValidationError


class ChangePartners(models.TransientModel):
    _name = "change.partners.wizard"
    _description = "Change partners wizard"
    _description = 'Change Partner wizard'

    @api.model
    def _get_active_model_name(self):
        return self.env.context.get('active_model', False)

    @api.model
    def _get_active_record(self, model_name):
        active_id = self.env.context.get('active_id', False)
        active_model = self.env.context.get('active_model', False)
        if active_id and active_model == model_name:
            return self.env[model_name].browse([active_id])
        return self.env[model_name]

    @api.model
    def _get_active_record_field(self, field_name):
        active_model = self.env.context.get('active_model', False)
        active_id = self.env.context.get('active_id', False)
        if active_model and active_id:
            record = self.env[active_model].browse([active_id])
            if hasattr(record, field_name):
                return getattr(record, field_name)
        return False

    name = fields.Char('Name')
    active_model_name = fields.Char(
        'Active model', default=lambda self: self._get_active_model_name())
    asset_id = fields.Many2one('grimm.asset.asset', string='Asset',
                               default=lambda self: self._get_active_record('grimm.asset.asset'), readonly=True)
    facility_id = fields.Many2one('grimm.asset.facility', string='Facility',
                                  default=lambda self: self._get_active_record('grimm.asset.facility'), readonly=True)
    update_children = fields.Boolean('Update Lower Levels')
    partner_owner = fields.Many2one(
        'res.partner', string='Owner', default=lambda self: self._get_active_record_field('partner_owner'))
    partner_object = fields.Many2one(
        'res.partner', string='Object', default=lambda self: self._get_active_record_field('partner_object'))
    partner_contact = fields.Many2one(
        'res.partner', string='Contact', default=lambda self: self._get_active_record_field('partner_contact'))
    partner_invoice = fields.Many2one(
        'res.partner', string='Invoice', default=lambda self: self._get_active_record_field('partner_invoice'))
    partner_delivery = fields.Many2one(
        'res.partner', string='Delivery', default=lambda self: self._get_active_record_field('partner_delivery'))
    beneficiary = fields.Many2one('res.partner', string='Beneficiary',
                                  default=lambda self: self._get_active_record_field('beneficiary'))

    def confirm(self):
        self.ensure_one()
        active_model = self.env.context.get('active_model', False)
        active_id = self.env.context.get('active_id', False)
        if active_model and active_id:
            record = self.env[active_model].browse([active_id])
            vals = {
                'partner_owner': self.partner_owner.id,
                'partner_object': self.partner_object.id,
                'partner_contact': self.partner_contact.id,
                'partner_invoice': self.partner_invoice.id,
                'partner_delivery': self.partner_delivery.id,
                'beneficiary': self.beneficiary,
            }
            record.write(vals)
            record.update_contact_addresses(vals, self.update_children)

        else:
            raise ValidationError(_('Missing data for active model or active id'))
