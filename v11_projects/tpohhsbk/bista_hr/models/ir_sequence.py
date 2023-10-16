# -*- encoding: utf-8 -*-

from odoo import fields, models,api,_
from datetime import datetime
from dateutil.relativedelta import relativedelta


class ir_sequence(models.Model):
    _inherit = 'ir.sequence'

    def _generate_sub_sequence_scheduler(self):
        """
            Generate monthly sequences for year wise.
        """
        sub_sequence_line = self.env['ir.sequence.date_range']
        use_date_range_rec = self.env['ir.sequence'].search([
            ('use_date_range', '=', True)
        ])
        for sequence in use_date_range_rec:
            year = fields.Date.from_string(fields.Date.today()).year
            for each_month in range(1,13):
                month_first_date = datetime(year=year, month=each_month, day=1)
                end_date = ((month_first_date + relativedelta(months=1, days=-1)).date()).strftime('%Y-%m-%d')
                start_date = (month_first_date.date()).strftime('%Y-%m-%d')
                sequence_line_rec = sub_sequence_line.search([
                    ('date_from', '=', start_date),
                    ('date_to', '=', end_date),
                    ('sequence_id', '=', sequence.id)
                ],limit=1)
                if not sequence_line_rec:
                    vals = {
                        'date_from': start_date,
                        'date_to': end_date,
                        'sequence_id': sequence.id
                    }
                    sub_sequence_line.create(vals)
