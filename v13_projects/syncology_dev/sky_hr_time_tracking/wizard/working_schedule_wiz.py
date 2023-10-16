from odoo import models, fields, api, _


class WorkingScheduleWizard(models.TransientModel):
    _name = 'working.schedule.wiz'
    _description = 'Working Schedule Wizard'

    schedule_id = fields.Many2one('resource.calendar', 'Working Schedule')

    def action_confirm(self):
        active_id = self._context.get('active_id')
        time_tacking = self.env['time.tracking'].browse(active_id)
        time_tacking.schedule_id = self.schedule_id
