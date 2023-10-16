from odoo import api, fields, models


class SaleReport(models.Model):
    _inherit = "sale.report"
    _description = "Sales Analysis Report"

    company_id = fields.Many2one('res.company', 'School', readonly=True)