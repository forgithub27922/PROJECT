from odoo import models, fields


class Project(models.Model):
    _inherit = 'project.task.type'

    set_default = fields.Boolean('It Is Default?')


class ProjectProject(models.Model):
    _inherit = 'project.project'

    type_ids = fields.Many2many('project.task.type',
                                default=lambda self: self._get_default())

    # def _get_default(self):
    #     task_type = self.env['project.task.type'].search([
    #         ('set_default', '=', True)])
    #
    #     vals = []
    #     for task in task_type:
    #         vals.append([(6, task)])
    #
    #     self.type_ids = vals

    def _get_default(self):
        type_ids = self.env['project.task.type'].search([
            ('set_default', '=', True)])
        return type_ids
