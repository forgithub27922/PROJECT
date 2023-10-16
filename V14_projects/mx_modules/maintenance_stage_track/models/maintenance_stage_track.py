# -*- coding: utf-8 -*-

from datetime import date, datetime, timedelta
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'

    date_last_stage_update = fields.Datetime('Last Stage Update', 
    	compute='_compute_date_last_stage_update', index=True, readonly=True, store=True)    

    @api.depends('stage_id')
    def _compute_date_last_stage_update(self):
        for rec in self:
            rec.date_last_stage_update = rec.create_date if not rec.date_last_stage_update else fields.Datetime.now()

    def write(self, vals):
        stage_origin_id = vals.get('stage_id') or False
        if stage_origin_id:
            for rec in self:
                stage_vals = {
                    'maintenance_id': rec.id,
                    'stage_origin_id': rec.stage_id and rec.stage_id.id,
                    'stage_dest_id': stage_origin_id,
                    'date_start': rec.date_last_stage_update,
                    'date_stop': fields.Datetime.now()
                }
                self.env['maintenance.stage.track'].create(stage_vals)
        return super(MaintenanceRequest, self).write(vals)


class MaintenanceStageTrack(models.Model):
    """ Model for case stages. This models the main stages of a Maintenance Request management flow. """
    _name = 'maintenance.stage.track'
    _description = 'Maintenance Stage Track'
    _order = 'date_stop desc, id'

    date_start = fields.Datetime(string="Date Start")
    date_stop = fields.Datetime(string="Date Stop")
    
    maintenance_id = fields.Many2one('maintenance.request', string='Maintenance Request')
    company_id = fields.Many2one('res.company', string='Company', related='maintenance_id.company_id', store=True,)
    maintenance_team_id = fields.Many2one('maintenance.team', string='Team', related='maintenance_id.maintenance_team_id', store=True)
    user_id = fields.Many2one('res.users', string='Technician', related='maintenance_id.user_id')
    name = fields.Char('Name', related='maintenance_id.name', store=True)
    maintenance_create_date = fields.Datetime(string="Created Date Maintenance", related='maintenance_id.create_date', store=True)

    owner_user_id = fields.Many2one('res.users', string='Created by User', default=lambda s: s.env.uid)
    stage_origin_id = fields.Many2one('maintenance.stage', string='Stage Origin', )
    stage_dest_id = fields.Many2one('maintenance.stage', string='Stage Destination', )
    done = fields.Boolean(related='stage_dest_id.done')

    days_calendar = fields.Float(string="Calendar days", compute='_compute_total_days_calendar', store=True)
    days_calendar_avg = fields.Float(string="Calendar days AVG", group_operator="avg", compute='_compute_total_days_calendar', store=True)
    days_working = fields.Float(string="Total working days")

    days_calendar_stage = fields.Float(string="Total calendar days on stage", compute='_compute_total_days_calendar', store=True)
    days_working_stage = fields.Float(string="Total working days on stage")
    hours_calendar_stage = fields.Float(string="Hours on stage", compute='_compute_total_days_calendar', store=True)
    hours_calendar_stage_avg = fields.Float(string="Hours on stage AVG", group_operator="avg", compute='_compute_total_days_calendar', store=True)
    hours_working_stage = fields.Float(string="Total working hours on stage")

    @api.depends('date_start', 'date_stop', 'maintenance_id')
    def _compute_total_days_calendar(self):
        for rec in self:
            if rec.maintenance_id:
                deltam = rec.date_stop - rec.maintenance_id.create_date
                deltas = rec.date_stop - rec.date_start
                tsecs = deltas.total_seconds()
                days = deltam.days
                rec.days_calendar = days
                rec.days_calendar_avg = days
                rec.days_calendar_stage = deltas.days
                rec.hours_calendar_stage = tsecs/(60*60)
                rec.hours_calendar_stage_avg = tsecs/(60*60)


# <field name="done" optional='hide' />
# kanban,tree,form,pivot,graph,calendar
