# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################
import re
from odoo import models, api, _
from odoo.exceptions import Warning


class hr_employee(models.Model):
    _inherit = 'hr.employee'

    @api.constrains('work_email')
    def _validate_email(self):
        if self.work_email and self.work_email != '':
            if not re.match("^[-a-zA-Z0-9._%+]+@[a-zA-Z0-9._%]+.[a-zA-Z]{2,6}$", self.work_email) is not None:
                raise Warning(_('Invalid Email. '
                                'Please enter a valid email address'))
