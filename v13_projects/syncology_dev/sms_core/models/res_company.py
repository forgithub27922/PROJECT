from odoo import models,fields,api


class ResCompany(models.Model):
    _inherit = 'res.company'

    synced_with_lms = fields.Boolean('Synced with LMS')
    lms_url = fields.Text('LMS URL')
    lms_url_token = fields.Text('LMS URL Token')
    admin_email = fields.Char('Email')
    scheduler_active = fields.Boolean('LMS Schedular')
