#########################################################################################
#
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#    Copyright (C) 2020 Skyscend Business Solutions Pvt. Ltd. (http://www.skyscendbs.com)
#
##########################################################################################
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import datetime


class TimeTrackingLine(models.Model):
    _inherit = 'time.tracking.line'

    approved_leave_start_time = fields.Float('Approved Leave Start Time')
    approved_leave_end_time = fields.Float('Approved Leave End Time')
    leave_id = fields.Many2one('hr.leave', 'Leave', domain=[('leave_type', '=', 'leave')])
    vacation_id = fields.Many2one('hr.leave', 'Vacation', domain=[('leave_type', '=', 'vacation')])



