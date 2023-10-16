# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    theme_color = fields.Char(string='Theme Color')
    col_1 = fields.Html(string='Column 1')
    col_2 = fields.Html(string='Column 2')
    col_3 = fields.Html(string='Column 3')
    col_4 = fields.Html(string='Column 4')

    report_logo_header = fields.Html(string='Report Logo and Header')

    @api.model
    def get_color_code(self, options={}):
        theme_color = "#875a7b" # Odoo default lay out color.
        for company in self.browse(options.get("allowed_company_ids",[])):
            return company.theme_color if company.theme_color else theme_color
        return theme_color


class ReportCompanyLabel(models.Model):
    _name = 'report.company.model'
    _description = 'Report company model'

    company_id = fields.Many2one('res.company',string="Company")
    report_id = fields.Many2one('ir.actions.report', string="Report ID")
    button_name = fields.Char(string='Button Name',required=True, translate=True)


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    button_label_ids = fields.One2many('report.company.model','report_id', string="Report Label")

    def read(self, fields=None, load='_classic_read'):
        res = super(IrActionsReport, self).read(fields=fields, load=load)
        for data in res:
            report_obj = self.browse(data["id"])
            for label in report_obj.button_label_ids:
                if label.company_id.id == self.env.user.company_id.id:
                    data["name"] = label.button_name
        return res
