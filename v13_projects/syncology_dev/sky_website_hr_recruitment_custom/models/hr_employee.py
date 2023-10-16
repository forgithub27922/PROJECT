from odoo import models, api

class Employee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def remove_website_group(self):
        self.env.ref("hr_recruitment.group_hr_recruitment_manager").implied_ids = [
            (3, self.env.ref('website.group_website_publisher').id)]