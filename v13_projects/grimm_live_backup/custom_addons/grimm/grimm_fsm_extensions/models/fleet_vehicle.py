#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  config.py
#
#  Copyright 2015 Grimm Gastrobedarf
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#

from odoo import api, fields, models, tools, _
from datetime import datetime, timedelta
import socket
import xmlrpc.client
import urllib.parse
import requests
import json
from requests.adapters import HTTPAdapter
from requests.auth import HTTPDigestAuth
from urllib3 import Retry
from random import randrange

import logging


_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    bornemann_id = fields.Char(string='Bornemann', required=True, readonly=True)

class FleetVehicleModel(models.Model):
    _inherit = 'fleet.vehicle.model'

    @api.depends('name', 'brand_id')
    def name_get(self):
        res = []
        for record in self:
            name = record.name
            if record.brand_id.name:
                name = record.brand_id.name + ' ' + name
            res.append((record.id, name))
        return res

class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    bornemann_id = fields.Many2one('bornemann.fleet', string="Bornemann Id")

    bornemann_partner_id = fields.Many2one('res.partner', string="Bornemann Partner Id", compute="_get_bornemann_partner_id")
    tuev_au_date = fields.Date(string='TÜV / AU')

    def _prepare_map_json(self, fleets):
        temp_list  = []
        for fleet in fleets:
            return_data = {}
            return_data["latitude"] = fleet.bornemann_partner_id.partner_latitude# + randrange(0,7)
            return_data["longitude"] = fleet.bornemann_partner_id.partner_longitude
            return_data["car_name"] = fleet.name
            return_data["driver_name"] = fleet.driver_id.name
            return_data["car_image"] = fleet.image_128
            return_data["bornemann_id"] = fleet.bornemann_id.bornemann_id
            temp_list.append(return_data)
        return temp_list
    @api.model
    def get_car_latlong(self, bornemann_id=False):
        if bornemann_id:
            bornemann_fleet = self.env['bornemann.fleet'].search([('bornemann_id', '=', bornemann_id)], limit=1)
            if bornemann_fleet:
                fleet_vehicles = self.env['fleet.vehicle'].search([('bornemann_id', '=', bornemann_fleet.id)])
                return self._prepare_map_json(fleet_vehicles)
        else:
            fleet_vehicles = self.env['fleet.vehicle'].search([('bornemann_id', '!=', False)])
            return self._prepare_map_json(fleet_vehicles)
        return False

    def _get_bornemann_partner_id(self):
        for record in self:
            record.bornemann_partner_id = False
            if record.bornemann_id.bornemann_id:
                bornemann_partner = self.env['res.partner'].search([('bornemann_id', '=', record.bornemann_id.bornemann_id)])
                if bornemann_partner:
                    record.bornemann_partner_id = bornemann_partner.id
                else:
                    bornemann_partner = self.env['res.partner'].create({"name": record.bornemann_id.name, "bornemann_id": record.bornemann_id.bornemann_id})
                    record.bornemann_partner_id = bornemann_partner.id
                configs = self.env['bornemann.config'].search([])
                for config in configs:
                    current_location = config.get_device_location(bornemann_id=record.bornemann_id.bornemann_id)
                    lon_lat = current_location.get("logLast").get("lonlat")
                    self._cr.execute("UPDATE res_partner set partner_latitude=%s,partner_longitude=%s where id=%s" % (lon_lat[1],lon_lat[0],bornemann_partner.id))

