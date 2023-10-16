# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import fields, models, api, _
from odoo.exceptions import Warning as UserError
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

class HrPublicHolidaysLine(models.Model):
    _name = 'hr.holidays.public.line'
    _description = 'Public Holidays Lines'
    _order = "date, name desc"

    name = fields.Char(
        'Name',
        required=True,
    )
    date = fields.Date(
        'Date',
        required=True
    )
    year_id = fields.Many2one(
        'hr.holidays.public',
        'Calendar Year',
        required=True,
    )
    variable = fields.Boolean('Date may change')
    state_ids = fields.Many2many(
        'res.country.state',
        'hr_holiday_public_state_rel',
        'line_id',
        'state_id',
        'Related States'
    )

    @api.multi
    @api.constrains('date', 'state_ids')
    def _check_date_state(self):
        for r in self:
            r._check_date_state_one()

    def _check_date_state_one(self):
        current_year = datetime.strptime(self.date,
                                         DEFAULT_SERVER_DATE_FORMAT).year
        if current_year != int(self.year_id.year):
            raise UserError(_(
                'Dates of holidays should be the same year '
                'as the calendar year they are being assigned to'
            ))
        if self.state_ids:
            domain = [('date', '=', self.date),
                      ('year_id', '=', self.year_id.id),
                      ('state_ids', '!=', False),
                      ('id', '!=', self.id)]
            holidays = self.search(domain)
            for holiday in holidays:
                if self.state_ids & holiday.state_ids:
                    raise UserError(_('You can\'t create duplicate public '
                                      'holiday per date %s and one of the '
                                      'country states.') % self.date)
        domain = [('date', '=', self.date),
                  ('year_id', '=', self.year_id.id),
                  ('state_ids', '=', False)]
        if self.search_count(domain) > 1:
            raise UserError(_('You can\'t create duplicate public holiday '
                            'per date %s.') % self.date)
        return True
