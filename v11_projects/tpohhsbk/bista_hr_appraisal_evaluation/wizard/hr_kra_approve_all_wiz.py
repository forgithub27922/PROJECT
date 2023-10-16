from odoo import models, api


class KraApproveAllWiz(models.TransientModel):
    _name = 'hr.kra.approve.all.wiz'

    @api.multi
    def approve_all_kra(self):
        for rec in self._context.get('active_ids'):
            appraisal = self.env['hr.employee.kra'].browse(rec)
            appraisal.self_eval_reviewed()
