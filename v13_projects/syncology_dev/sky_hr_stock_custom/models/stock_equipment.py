from odoo import fields, models, api, _

class StockEquipment(models.Model):
    _name = 'stock.equipment'
    _description = 'Stock Equipment'
    _rec_name = 'unit'

    @api.depends('employee_id.first_name_arabic', 'employee_id.middle_name_arabic', 'employee_id.last_name_arabic', 'employee_id.fourth_name_arabic')
    def _compute_employee_name_arabic(self):
        for equipment in self:
            equipment.employee_arabic_name = str(equipment.employee_id.first_name_arabic) + " " + str(equipment.employee_id.middle_name_arabic) + " " + str(equipment.employee_id.last_name_arabic) + " " + str(equipment.employee_id.fourth_name_arabic)
    
    unit = fields.Many2one('product.product', string='Unit')
    quantity = fields.Float(string='Quantity')
    date = fields.Date(string='Date')
    cost_of_damage = fields.Float(string='Cost Of Damage')
    status = fields.Many2one('stock.status', string='Status')
    employee_id = fields.Many2one('hr.employee', 'Employee')
    employee_arabic_name = fields.Char('Employee (Arabic)', compute="_compute_employee_name_arabic", tracking=True, store=True)


class StockStatus(models.Model):
    _name = 'stock.status'
    _description = 'Stock Status'
    _rec_name = 'name'

    name = fields.Char('Name')
    code = fields.Char('Code')