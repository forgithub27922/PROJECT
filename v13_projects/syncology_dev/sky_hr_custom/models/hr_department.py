#########################################################################################
#
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#    Copyright (C) 2020 Skyscend Business Solutions Pvt. Ltd. (http://www.skyscendbs.com)
#
##########################################################################################
from odoo import models, fields, api


class Department(models.Model):
    _inherit = 'hr.department'

    working_schedule_id = fields.Many2one('resource.calendar', 'Working Schedule')
    business_hours = fields.Float("Business Hours")

    def write(self, vals):
        """
        Overridden write method to update the working schedule of particular department employees
        -----------------------------------------------------------------------------------------
        @param self: object pointer
        @param vals: dictionary containing fields and values
        :return: True
        """
        res = super(Department, self).write(vals)
        employee_obj = self.env['hr.employee']
        for dept in self:
            if vals.get('working_schedule_id', False):
                employees = employee_obj.search([('department_id', '=', dept.id)])
                employees.write({'resource_calendar_id': vals.get('working_schedule_id')})
        return res
