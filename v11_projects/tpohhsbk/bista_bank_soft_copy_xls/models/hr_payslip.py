from odoo import models, fields, api, _


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    @api.depends('line_ids')
    def compute_net_amount(self):
        for rec in self:
            amount = 0
            conf_obj = self.env['ir.config_parameter']
            code = conf_obj.get_param('bank_soft_copy_amount_code')
            if code:
                for line in rec.line_ids:
                    if code == line.code:
                        amount += line.amount
            rec.net_amount = amount

    net_amount = fields.Float('Net Amount', compute='compute_net_amount')