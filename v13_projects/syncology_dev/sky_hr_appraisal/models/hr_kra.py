#########################################################################################
#
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#    Copyright (C) 2020 Skyscend Business Solutions Pvt. Ltd. (http://www.skyscendbs.com)
#
##########################################################################################
from odoo import models, fields, api


class KRAOptions(models.Model):
    _name = 'hr.kra.options'
    _description = 'KRA Options'

    name = fields.Char('Description')
    kra_id = fields.Many2one('hr.kra', 'KRA')
    value = fields.Integer('Value')


class KRA(models.Model):
    _name = 'hr.kra'
    _description = 'Key Result Area (KRA)'

    name = fields.Char('Name')
    department_id = fields.Many2one('hr.department', 'Department')
    job_id = fields.Many2one('hr.job', 'Job Position')
    active = fields.Boolean('Active', default=True)
    option_ids = fields.One2many('hr.kra.options', 'kra_id', 'Options')



