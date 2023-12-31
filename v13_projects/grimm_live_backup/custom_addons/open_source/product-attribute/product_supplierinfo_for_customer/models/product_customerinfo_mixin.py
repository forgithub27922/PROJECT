# Copyright 2021 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class ProductSupplierInfoMixin(models.AbstractModel):
    _name = "product.customerinfo.mixin"
    _description = "Common methods to compute prices based on partners"

    def _get_price_from_customerinfo(self, partner_id):
        self.ensure_one()
        if not partner_id:
            return 0.0
        partner = self.env["res.partner"].browse(partner_id)
        customerinfo = self._select_customerinfo(partner=partner)
        if customerinfo:
            return customerinfo.price
        return 0.0

    def get_customerinfo_price(self, uom=False, currency=False, company=False):
        partner_id = self.env.context.get("partner_id", False) or self.env.context.get(
            "partner", False
        )
        if partner_id and isinstance(partner_id, models.BaseModel):
            partner_id = partner_id.id
        prices = self.price_compute("list_price", uom, currency, company)
        for product in self:
            price = product._get_price_from_customerinfo(partner_id)
            if not price:
                continue
            prices[product.id] = price
            if not uom and self._context.get("uom"):
                uom = self.env["uom.uom"].browse(self._context["uom"])
            if not currency and self._context.get("currency"):
                currency = self.env["res.currency"].browse(self._context["currency"])
            if uom:
                prices[product.id] = product.uom_id._compute_price(
                    prices[product.id], uom
                )
            if currency:
                date = self.env.context.get("date", fields.Datetime.now())
                prices[product.id] = product.currency_id._convert(
                    prices[product.id], currency, company, date
                )
        return prices

    def _prepare_domain_customerinfo(self, params):
        self.ensure_one()
        partner_id = params.get("partner_id")
        if self._name == "product.template":
            return [
                ("name", "=", partner_id),
                ("product_tmpl_id", "=", self.id),
            ]
        else:
            return [
                ("name", "=", partner_id),
                "|",
                ("product_id", "=", self.id),
                "&",
                ("product_tmpl_id", "=", self.product_tmpl_id.id),
                ("product_id", "=", False),
            ]

    def _select_customerinfo(
        self, partner=False, _quantity=0.0, _date=None, _uom_id=False, params=False
    ):
        """Customer version of the standard `_select_seller`. """
        # TODO: For now it is just the function name with same arguments, but
        #  can be changed in future migrations to be more in line Odoo
        #  standard way to select supplierinfo's.
        if not params:
            params = dict()
        params.update({"partner_id": partner.id})
        domain = self._prepare_domain_customerinfo(params)
        res = (
            self.env["product.customerinfo"]
            .sudo()
            .search(domain, order="product_id, sequence", limit=1)
        )
        return res
