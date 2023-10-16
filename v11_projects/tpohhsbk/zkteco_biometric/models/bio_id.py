# -*- coding: utf-8 -*-
##############################################################################
#
# Skyscend Business Soluitions
# Copyright (C) 2019  (http://www.skyscendbs.com)
#
# Skyscend Business Soluitions Pvt. Ltd.
# Copyright (C) 2020  (http://www.skyscendbs.com)
##############################################################################
from odoo import models, fields, api, exceptions, _


class hr_employee_inherited_bio(models.Model):
    """
    For the Biometric ID at the HR Employee
    """
    _inherit = "hr.employee"
    _description = "Employee"

    bioid = fields.Char(string="Biometric ID")  # Biometric ID

    _sql_constraints = [('bioid_uniq', 'unique (bioid)', "The Biometric ID must be unique, this one is already assigned to another employee.")]
