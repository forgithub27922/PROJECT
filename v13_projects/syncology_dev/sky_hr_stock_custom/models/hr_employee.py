from odoo import fields, models, api, _

class Employee(models.Model):
    _inherit = 'hr.employee'

    equipment_ids = fields.One2many('stock.equipment', 'employee_id', string='Employees Handover')






