# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class FleetAttachmentCategory(models.Model):
    _name = 'fleet.attachment.category'
    _description = 'Fleet attachment category'

    created_on = fields.Datetime(
        string='Created On',
        # default=lambda self: self._default_date(),
    )

    description = fields.Text(string='Description')
    valid_from = fields.Date(string='Valid From')
    valid_to = fields.Date(string='Valid To')
    fleet_vehicle_angebot = fields.Many2one('fleet.vehicle', string='Fleet Vehicle')
    fleet_vehicle_vertrag = fields.Many2one('fleet.vehicle', string='Fleet Vehicle')
    fleet_vehicle_zulassung = fields.Many2one('fleet.vehicle', string='Fleet Vehicle')
    fleet_vehicle_reparature = fields.Many2one('fleet.vehicle', string='Fleet Vehicle')
    fleet_vehicle_steuer = fields.Many2one('fleet.vehicle', string='Fleet Vehicle')
    fleet_vehicle_accidents = fields.Many2one('fleet.vehicle', string='Fleet Vehicle')
    fleet_vehicle_sondereinbauten = fields.Many2one('fleet.vehicle', string='Fleet Vehicle')
    fleet_vehicle_verkauf = fields.Many2one('fleet.vehicle', string='Fleet Vehicle')
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    fleet_attach_angebot = fields.One2many('fleet.attachment.category', 'fleet_vehicle_angebot', string='Fleet Attachment')
    fleet_attach_vertrag = fields.One2many('fleet.attachment.category', 'fleet_vehicle_vertrag', string='Fleet Attachment')
    fleet_attach_zulassung = fields.One2many('fleet.attachment.category', 'fleet_vehicle_zulassung', string='Fleet Attachment')
    fleet_attach_reparaturen = fields.One2many('fleet.attachment.category', 'fleet_vehicle_reparature', string='Fleet Attachment')
    fleet_attach_steuer = fields.One2many('fleet.attachment.category', 'fleet_vehicle_steuer', string='Fleet Attachment')
    fleet_attach_accidents = fields.One2many('fleet.attachment.category', 'fleet_vehicle_accidents', string='Fleet Attachment')
    fleet_attach_sondereinbauten = fields.One2many('fleet.attachment.category', 'fleet_vehicle_sondereinbauten', string='Fleet Attachment')
    fleet_attach_verkauf = fields.One2many('fleet.attachment.category', 'fleet_vehicle_verkauf', string='Fleet Attachment')
    garage = fields.Char('Garage')
    leasingablauf = fields.Date(string='Leasingablauf')
    vereinbarte_kilometer = fields.Integer('Vereinbarte Kilometer')
    letzter_fahrzeugcheck = fields.Date(string='Letzter Fahrzeugcheck')
    tuev_au = fields.Char(string='TÜV / AU')
