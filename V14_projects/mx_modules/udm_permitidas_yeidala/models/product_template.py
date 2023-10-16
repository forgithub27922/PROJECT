# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api
from odoo.osv import expression


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    uom_category_id = fields.Many2one(related="uom_po_id.category_id", string='Udm Category')
    uom_allowed_ids = fields.Many2many('uom.uom', string='UdM Permitidos', domain="[('category_id','=',uom_category_id)]")


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    uom_allowed_ids = fields.Many2many(related="product_id.uom_allowed_ids", string='UdM Permitidos')

class PurchaseRequestLine(models.Model):
    _inherit = 'purchase.request.line'

    uom_allowed_ids = fields.Many2many(related="product_id.uom_allowed_ids", string='UdM Permitidos')

    @api.onchange("product_id")
    def onchange_product_id(self):
        res = super().onchange_product_id()
        if self.product_id:
            self.product_uom_id = self.product_id.uom_po_id.id

# stock.warehouse.orderpoint

class Orderpoint(models.Model):
    _inherit = "stock.warehouse.orderpoint"

    uom_allowed_ids = fields.Many2many(related="product_id.uom_allowed_ids", string='UdM Permitidos')
    procure_uom_id = fields.Many2one(comodel_name="uom.uom", string="Procurement UoM")

class ProcurementGroup(models.Model):
    _inherit = "procurement.group"

    @api.model
    def run(self, procurements, raise_user_error=True):
        # 'Procurement' is a 'namedtuple', which is not editable.
        # The 'procurement' which needs to be edited is created new
        # and the previous one is deleted.
        Proc = self.env["procurement.group"].Procurement
        indexes_to_pop = []
        new_procs = []
        for i, procurement in enumerate(procurements):
            if "orderpoint_id" in procurement.values:
                orderpoint = procurement.values.get("orderpoint_id")
                if (
                    orderpoint.procure_uom_id
                    and procurement.product_uom != orderpoint.procure_uom_id
                ):
                    new_product_qty = procurement.product_uom._compute_quantity(
                        procurement.product_qty, orderpoint.procure_uom_id
                    )
                    new_product_qty = procurement.product_qty
                    new_product_uom = orderpoint.procure_uom_id
                    new_procs.append(
                        Proc(
                            procurement.product_id,
                            new_product_qty,
                            new_product_uom,
                            procurement.location_id,
                            procurement.name,
                            procurement.origin,
                            procurement.company_id,
                            procurement.values,
                        )
                    )
                    indexes_to_pop.append(i)
        if new_procs:
            indexes_to_pop.reverse()
            for index in indexes_to_pop:
                procurements.pop(index)
        procurements.extend(new_procs)
        return super(ProcurementGroup, self).run(procurements, raise_user_error)