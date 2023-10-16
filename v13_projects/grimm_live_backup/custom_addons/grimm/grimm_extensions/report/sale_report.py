# -*- coding: utf-8 -*-


from odoo import models


class SaleReport(models.Model):
    _inherit = 'sale.report'

    def _from(self):
        from_str = super(SaleReport, self)._from()
        from_str = from_str + ' LEFT JOIN sale_layout_category AS slc ON l.layout_category_id = slc.id'
        return from_str

    def _group_by(self):
        group_str = super(SaleReport, self)._group_by()
        group_str = " WHERE slc.add_to_total = 't' OR slc.id is null " + group_str
        return group_str
