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

class ChannelMessage(models.Model):
    _name = 'channel.message'

    message_id = fields.Many2one('mail.message', string='Message ID')
    user_id = fields.Many2one('res.users', string='User ID')

    _sql_constraints = [('message_user_unique', 'unique (message_id,user_id)',
                         'There should be unique message entry per user.')]

class MailMessage(models.Model):
    _inherit = 'mail.message'

    need_to_display = fields.Boolean("Is Display?", compute="_is_need_to_display")

    def _is_need_to_display(self):
        for record in self:
            record.need_to_display = False if self.env['channel.message'].search_count([('user_id', '=', self.env.user.id),('message_id', '=', record.id)]) > 0 else True

    def _get_message_format_fields(self):
        field_list = super(MailMessage, self)._get_message_format_fields()
        field_list.append("need_to_display")

    def set_channel_message_done(self):
        """ Remove the needaction from messages for the current partner. """
        partner_id = self.env.user.partner_id
        try:
            new_id = self.env['channel.message'].sudo().create({'message_id':self.id,'user_id':self.env.user.id})
        except Exception as e:
            _logger.warn(str(e))