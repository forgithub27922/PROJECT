# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class SeviceTravel(models.Model):
    _name = 'service.travel'
    _description = 'Service Travel'

    st_small_pieces = fields.Boolean('Kleineteile / Befestigung / Pflege')
    st_meters_pack = fields.Boolean('Messgerätepauschale')
    st_clean_and_care = fields.Boolean('Reinigungs- und Pflegematerial')
    task_id = fields.Many2one('project.task', string='Task ID')
    user_id = fields.Many2one('res.users', string='User')
    # other_material = fields.Text('Other Material')
    # date = fields.Datetime('Date')


class ServiceTravelTimesheet(models.Model):
    _name = 'service.travel.timesheet'
    _description = 'Service travel timesheet'

    travel_cost = fields.Selection([('anfahrtspauschale berlin (ap i)', 'Anfahrtspauschale Berlin (AP I)'),
                                    ('anfahrtspauschale ii (ap 2)', 'Anfahrtspauschale II (AP 2)'),
                                    ('keine anfahrt', 'Keine Anfahrt')], string='Anfahrtspauschale', default='anfahrtspauschale berlin (ap i)')
    duration = fields.Float('Arbeitszeit')
    date = fields.Datetime('Date')
    task_id = fields.Many2one('project.task', string='Task ID')
    user_id = fields.Many2one('res.users', string='User')
    other_material = fields.Text('Other Material')
