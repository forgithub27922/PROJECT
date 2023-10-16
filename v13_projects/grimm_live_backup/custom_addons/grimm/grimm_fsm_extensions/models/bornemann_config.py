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
from odoo.addons.connector.exception import NetworkRetryableError
from urllib3 import Retry
import logging


_logger = logging.getLogger(__name__)

class BornemannFleet(models.Model):
    _name = 'bornemann.fleet'
    name = fields.Char(string='Name', required=True, readonly=True)
    bornemann_id = fields.Char(string='Bornemann', required=True, readonly=True)

    _sql_constraints = [
        ('match_bornemann_id_uniq', 'unique(bornemann_id)', 'Bornemann Id must be unique !'),
    ]

    def name_get(self):
        res = []
        for fleet in self:
            res.append((fleet.id, "%s - (%s)"%(fleet.name,fleet.bornemann_id)))
        return res

class BornemannConfig(models.Model):
    _name = 'bornemann.config'

    name = fields.Char(string='Name', required=True)
    version = fields.Char(string='Version', readonly=True)
    location = fields.Char(
        string='Location',
        required=True,
        help="Url to Bornemann application",
    )
    token = fields.Char(
        string='API Token',
        help="Webservice API Token",
    )
    is_print_log = fields.Boolean(
        string='Log API call?',
        help="It will log api call in logger file.",
    )

    def synchronize_metadata(self):
        return_data = self._call(method="GET",api_call="%s/data/assets/all"%self.location)
        for fleet in return_data:
            bornemann_fleet = self.env['bornemann.fleet'].search([('bornemann_id', '=', fleet.get("_id"))])
            if bornemann_fleet:
                bornemann_fleet.name = fleet.get("name","")
            else:
                new_bornemann_fleet_id = self.env['bornemann.fleet'].create({"name":fleet.get("name"),"bornemann_id":fleet.get("_id")})

    def get_device_location(self, bornemann_id=False):
        if bornemann_id:
            return_data = self._call(method="GET", api_call="%s/data/assets/%s"%(self.location, bornemann_id))
            return return_data

    def _call(self, method="GET", api_call = False):
        try:
            start = datetime.now()
            method = method.upper()
            timeout = 6
            headers = {'Authorization': 'Bearer %s'%self.token, 'Accept': '*/*'}
            if self.is_print_log:
                _logger.info("\n=====Called final Bornemann api call is ===> %s %s with header ==> %s"%(method, self.location, headers))
            response = requests.get(api_call, headers=headers, timeout=timeout)
            if self.is_print_log:
                _logger.info("Response code is ===> %s" % response)
            response_code = response.status_code
            try:
                if self.is_print_log:
                    _logger.info("\n\nReturn response from Bornemann is ===> %s" % response.content.decode('utf-8'))
                if response_code >= 200 and response_code <= 299:
                    result = response.json()
                else:
                    raise FailedJobError(
                        "Odoo received error from Bornemann.\n\n%s" % (response.content.decode('utf-8')))
            except:
                _logger.error("api.call('%s %s') failed" % (method, self.location))
                raise
            else:
                _logger.debug(
                    "api.call('%s') returned in %s seconds" % (self.location, (datetime.now() - start).seconds))
            return result
        except (socket.gaierror, socket.error, socket.timeout) as err:
            raise NetworkRetryableError(
                'A network error caused the failure of the job: '
                '%s ==== %s %s' % (err, method, self.location))
        except xmlrpc.client.ProtocolError as err:
            if err.errcode in [502,   # Bad gateway
                               503,   # Service unavailable
                               504]:  # Gateway timeout
                raise NetworkRetryableError(
                    'A network error caused the failure of the job: '
                    '%s ==== %s %s' % (err, method, self.location))
            else:
                raise
