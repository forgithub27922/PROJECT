from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PurchaseRequestUnitOfMeasure(models.TransientModel):
	_inherit = "purchase.request.line.make.purchase.order"

	@api.model
	def _prepare_purchase_order_line(self, po, item):
		
		if not item.product_id:
			raise UserError(_("Please select a product for all lines"))
		product = item.product_id

		# Keep the standard product UOM for purchase order so we should
		# convert the product quantity to this UOM
		
		qty = item.product_uom_id._compute_quantity(
			item.product_qty, product.uom_po_id or product.uom_id
		)
		
			

		# Suggest the supplier min qty as it's done in Odoo core
		date_required = item.line_id.date_required
		vals = {
			"name": product.name,
			"order_id": po.id,
			"product_id": product.id,
			"product_uom": item.product_uom_id.id or product.uom_id.id,
			"price_unit": 0.0,
			# "product_qty": item.product_qty,
			"product_qty": qty,
			"account_analytic_id": item.line_id.analytic_account_id.id,
			"purchase_request_lines": [(4, item.line_id.id)],
			"date_planned": datetime(
				date_required.year, date_required.month, date_required.day
			),
			"move_dest_ids": [(4, x.id) for x in item.line_id.move_dest_ids],
		}
		if item.line_id.analytic_tag_ids:
			vals["analytic_tag_ids"] = [
				(4, ati) for ati in item.line_id.analytic_tag_ids.ids
			]
		self._execute_purchase_line_onchange(vals)
		return vals


	def make_purchase_order(self):
	
		res = []
		purchase_obj = self.env["purchase.order"]
		po_line_obj = self.env["purchase.order.line"]
		pr_line_obj = self.env["purchase.request.line"]
		purchase = False

		for item in self.item_ids:
			line = item.line_id
			if item.product_qty <= 0.0:
				raise UserError(_("Enter a positive quantity."))
			if self.purchase_order_id:
				purchase = self.purchase_order_id
			if not purchase:
				po_data = self._prepare_purchase_order(
					line.request_id.picking_type_id,
					line.request_id.group_id,
					line.company_id,
					line.origin,
				)
				purchase = purchase_obj.create(po_data)

			# Look for any other PO line in the selected PO with same
			# product and UoM to sum quantities instead of creating a new
			# po line
			domain = self._get_order_line_search_domain(purchase, item)
			available_po_lines = po_line_obj.search(domain)
			new_pr_line = True
			# If Unit of Measure is not set, update from wizard.
			if not line.product_uom_id:
				line.product_uom_id = item.product_uom_id
			# Allocation UoM has to be the same as PR line UoM
			alloc_uom = line.product_uom_id
			wizard_uom = item.product_uom_id
			if available_po_lines and not item.keep_description:
				
				new_pr_line = False
				po_line = available_po_lines[0]
				po_line.purchase_request_lines = [(4, line.id)]
				po_line.move_dest_ids |= line.move_dest_ids
				
				po_line_product_uom_qty = po_line.product_uom._compute_quantity(
					po_line.product_uom_qty, alloc_uom
				)
				
				wizard_product_uom_qty = wizard_uom._compute_quantity(
					item.product_qty, alloc_uom
				)
				all_qty = min(po_line_product_uom_qty, wizard_product_uom_qty)
				self.create_allocation(po_line, line, all_qty, alloc_uom)
			else:
				
				po_line_data = self._prepare_purchase_order_line(purchase, item)
				if item.keep_description:
					po_line_data["name"] = item.name
				po_line = po_line_obj.create(po_line_data)

				
				po_line_product_uom_qty = alloc_uom._compute_quantity(
					po_line.product_uom_qty, po_line.product_uom
				)
				
				wizard_product_uom_qty = wizard_uom._compute_quantity(
					item.product_qty, alloc_uom
				)
				all_qty = max(po_line_product_uom_qty, wizard_product_uom_qty)
				self.create_allocation(po_line, line, all_qty, alloc_uom)

			# TODO: Check propagate_uom compatibility:
			
			# The onchange quantity is altering the scheduled date of the PO
			# lines. We do not want that:
			date_required = item.line_id.date_required
			po_line.date_planned = datetime(
				date_required.year, date_required.month, date_required.day
			)
			res.append(purchase.id)

		return {
			"domain": [("id", "in", res)],
			"name": _("RFQ"),
			"view_mode": "tree,form",
			"res_model": "purchase.order",
			"view_id": False,
			"context": False,
			"type": "ir.actions.act_window",
		}