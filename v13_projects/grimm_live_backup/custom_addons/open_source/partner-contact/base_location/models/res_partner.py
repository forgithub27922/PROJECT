# Copyright 2016 Nicolas Bessi, Camptocamp SA
# Copyright 2018-2023 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    zip_id = fields.Many2one("res.city.zip", "ZIP Location", index=True)
    city_id = fields.Many2one(index=True)  # add index for performance

    @api.onchange("city_id")
    def _onchange_city_id(self):
        if not self.zip_id:
            super()._onchange_city_id()
        if self.zip_id and self.city_id != self.zip_id.city_id:
            self.update({"zip_id": False, "zip": False, "city": False})
        if self.city_id and self.country_enforce_cities:
            return {"domain": {"zip_id": [("city_id", "=", self.city_id.id)]}}
        return {"domain": {"zip_id": []}}

    @api.onchange("country_id")
    def _onchange_country_id(self):
        res = super()._onchange_country_id()
        if self.zip_id and self.zip_id.city_id.country_id != self.country_id:
            self.zip_id = False
        return res

    @api.onchange("zip_id")
    def _onchange_zip_id(self):
        if self.zip_id:
            vals = {
                "city_id": self.zip_id.city_id,
                "zip": self.zip_id.name,
                "city": self.zip_id.city_id.name,
            }
            if self.zip_id.city_id.country_id:
                vals.update({"country_id": self.zip_id.city_id.country_id})
            if self.zip_id.city_id.state_id:
                vals.update({"state_id": self.zip_id.city_id.state_id})
            self.update(vals)
        elif not self.country_enforce_cities:
            self.city_id = False

    @api.constrains("zip_id", "country_id", "city_id", "state_id")
    def _check_zip(self):
        if self.env.context.get("skip_check_zip"):
            return
        for rec in self:
            if not rec.zip_id:
                continue
            if rec.zip_id.city_id.state_id != rec.state_id:
                raise ValidationError(
                    _("The state of the partner %s differs from that in " "location %s")
                    % (rec.name, rec.zip_id.name)
                )
            if rec.zip_id.city_id.country_id != rec.country_id:
                raise ValidationError(
                    _(
                        "The country of the partner %s differs from that in "
                        "location %s"
                    )
                    % (rec.name, rec.zip_id.name)
                )
            if rec.zip_id.city_id != rec.city_id:
                raise ValidationError(
                    _("The city of partner %s differs from that in " "location %s")
                    % (rec.name, rec.zip_id.name)
                )

    @api.onchange("state_id")
    def _onchange_state_id(self):
        vals = {}
        if self.state_id.country_id:
            vals.update({"country_id": self.state_id.country_id})
        if self.zip_id and self.state_id != self.zip_id.city_id.state_id:
            vals.update({"zip_id": False, "zip": False, "city": False})
        self.update(vals)

    @api.model
    def _address_fields(self):
        return super()._address_fields() + ["zip_id"]

    @api.model
    def _fields_view_get_address(self, arch):
        """Force the save of the city_id field, as we set it through the onchanges
        and we need consistency (there's a constraint for that).
        """
        arch = super()._fields_view_get_address(arch)
        doc = etree.fromstring(arch)
        for node in doc.xpath("//field[@name='city_id']"):
            node.attrib["force_save"] = "1"
        arch = etree.tostring(doc, encoding="unicode")
        return arch
