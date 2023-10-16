from odoo import models, fields, api


class PublicHolidaysLine(models.Model):
    _name = 'hr.public.holidays.line'
    _description = 'Public Holidays'

    date = fields.Date('Date')
    day = fields.Selection([('0', 'Monday'),
                             ('1', 'Tuesday'),
                             ('2', 'Wednesday'),
                             ('3', 'Thursday'),
                             ('4', 'Friday'),
                             ('5', 'Saturday'),
                             ('6', 'Sunday')], 'Weekday')
    name = fields.Char('Occasion')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)

    @api.onchange('date')
    def onchange_date(self):
        """
        This method is used to set the weekday depending on the date selected.
        ----------------------------------------------------------------------
        @param self: object pointer
        """
        for pub_holiday in self:
            if pub_holiday.date:
                pub_holiday.day = str(pub_holiday.date.weekday())



