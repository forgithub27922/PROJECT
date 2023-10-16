from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    synced_with_lms = fields.Boolean('Synced with LMS',related='company_id.synced_with_lms', readonly=False)
    lms_url = fields.Text('LMS URL', related='company_id.lms_url', readonly=False)
    lms_url_token = fields.Text('LMS URL Token', related='company_id.lms_url_token', readonly=False)
    admin_email = fields.Char(string='Email', related='company_id.admin_email', readonly=False)


    @api.model
    def create(self, vals):
        res = super(ResConfigSettings, self).create(vals)
        # to remove lms menu
        group_list = []
        groups_ids = self.env['res.groups'].search([])
        for group in groups_ids:
            group_list.append(group.id)
        user_ids = self.env['res.users'].search([('groups_id', 'in', group_list)])
        group_id = self.env.ref('sms_core.group_lms_sync')
        if self.env.company.synced_with_lms:
            group_id.users = [(4, user.id) for user in user_ids]
        else:
            group_id.users = [(3, user.id) for user in user_ids]

        # Schools, Grades, Classes should have “Create” button
        for group in groups_ids:
            for lines in group.model_access:
                if lines.name in ['school.class', 'class.section', 'schools.list']:
                    if not self.env.company.synced_with_lms:
                        if group.name != 'Settings':
                            lines.perm_create = True
                    else:
                        if group.name == 'Student Affairs Manager' and lines.name == 'schools.list' or 'class.section':
                            lines.perm_create = False
                        if group.name == 'Student Affairs Officer' and lines.name == 'schools.list':
                            lines.perm_create = False

        return res
