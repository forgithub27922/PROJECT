# -*- coding: utf-8 -*-

from odoo import models, api


class ProductCategory(models.Model):
    _inherit = 'product.category'

    def get_child_ids(self):
        res = []
        for record in self:
            res.append(record.id)
            if record.child_id:
                res.extend(record.child_id.get_child_ids())
        res = set(res)
        res = list(res)
        return res

    @api.model
    @api.returns('self',
                 upgrade=lambda self, value, args, offset=0, limit=None, order=None,
                                count=False: value if count else self.browse(value),
                 downgrade=lambda self, value, args, offset=0, limit=None, order=None,
                                  count=False: value if count else value.ids)
    def search(self, args, offset=0, limit=None, order=None, count=False):
        is_search_by_name = False
        for arg in args:
            if type(arg) in [list, set, tuple]:
                if arg[0] == 'name':
                    is_search_by_name = True
        res = super(ProductCategory, self).search(args, offset=offset, limit=limit, order=order, count=count)
        if is_search_by_name:
            child_ids = res.get_child_ids()
            res = self.browse(child_ids)

        return res
