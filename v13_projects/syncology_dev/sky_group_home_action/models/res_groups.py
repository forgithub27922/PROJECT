from odoo import models, fields, api


class ResGroups(models.Model):
    _inherit = 'res.groups'

    home_action_id = fields.Many2one('ir.actions.actions', 'Home Action')
    action_priority = fields.Integer('Action Priority', default=10)

    @api.model_create_multi
    def create(self, vals_list):
        res = super(ResGroups, self).create(vals_list)
        res.users.set_home_action()
        return res

    def write(self, vals):
        users = self.env['res.users']
        for group in self:
            users += group.users
        res = super(ResGroups, self).write(vals)
        users.set_home_action()
        return res


class ResUsers(models.Model):
    _inherit = 'res.users'

    def set_home_action(self):
        for user in self:
            priority = 0
            action = False
            for group in user.groups_id:
                if group.home_action_id:
                    if priority < group.action_priority:
                        priority = group.action_priority
                        action = group.home_action_id.id
            user.with_context(from_write=True).write({'action_id': action})

    @api.model_create_multi
    def create(self, vals_list):
        res = super(ResUsers, self).create(vals_list)
        res.set_home_action()
        return res

    def write(self, vals):
        res = super(ResUsers, self).write(vals)
        if not self._context.get('from_write'):
            self.set_home_action()
        return res

