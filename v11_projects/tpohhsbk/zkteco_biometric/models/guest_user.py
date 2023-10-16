# -*- coding: utf-8 -*-
##############################################################################
#
# Skyscend Business Soluitions
# Copyright (C) 2019  (http://www.skyscendbs.com)
#
# Skyscend Business Soluitions Pvt. Ltd.
# Copyright (C) 2020  (http://www.skyscendbs.com)
##############################################################################
from odoo import models, fields, api, exceptions, _



class guest_user(models.Model):
    """
    Guest User
    """
    _name = 'guest.user'
    _order = "guest_datetime desc"
    _rec_name = "guest_userid"
    _description = "Guest Attendance"

    guest_userid = fields.Char(string='Guest Bio-ID', readonly=True)
    guest_datetime = fields.Datetime(string='Guest Datetime', readonly=True)
    guest_action = fields.Char(string='Guest Action', readonly=True)


class last_attn(models.Model):
    """
    Last Attendance
    """
    _name = 'last.attn'
    _order = "last_dt desc"
    _rec_name = "last_dt"
    _description = "Last attendance"

    last_dt = fields.Datetime(string='Last Attendance', readonly=True)