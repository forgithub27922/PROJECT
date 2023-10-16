
from odoo import models, fields, api, tools


class PrintReportWizard(models.TransientModel):
    _name = 'print.report.wizard'
    _description = 'Print Report Wizard'

    download_file = fields.Binary('Download File', readonly=True)
    fname = fields.Char('File Name')
