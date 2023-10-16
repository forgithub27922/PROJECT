from odoo import fields, models, api, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    contact_type = fields.Selection([('student', 'Student'), ('employee', 'Employee'), ('external', 'External')], string='Contact Type')
    student_id = fields.Many2one('academic.student', 'Contact', domain=[('moodle_status', '=', 'active')])
    employee_id = fields.Many2one('hr.employee', 'Contact', domain=[('active', '=', True)])
    partner_id = fields.Many2one('res.partner', 'Contact')
    status_id = fields.Many2one('stock.status', 'Status')

    @api.onchange('student_id')
    def onchange_student_id(self):
        """
        Onchange method to set partner_id based on student_id
        -----------------------------------------------------
        :param self: object pointer
        """
        if self.student_id:
            self.partner_id = self.student_id.partner_id

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        """
        Onchange method to set partner_id based on employee_id
        ------------------------------------------------------
        :param self: object pointer
        """
        if self.employee_id:
            self.partner_id = self.employee_id.user_id.partner_id
