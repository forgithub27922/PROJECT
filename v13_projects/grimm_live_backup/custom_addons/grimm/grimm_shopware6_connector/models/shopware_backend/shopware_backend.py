# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2016 Openfellas (http://openfellas.com) All Rights Reserved.
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsibility of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# guarantees and support are strongly advised to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

# from ..unit.product_import import prepare_nonconfig_product_prices_batch_import
import logging
import json
from datetime import datetime, timedelta

from odoo import models, fields, api, _
from odoo.exceptions import Warning

_logger = logging.getLogger(__name__)

# -*- coding: utf-8 -*-

from odoo import models, api

class AutoRepliedEmail(models.Model):
    _name = 'auto.replied.email'

    name = fields.Char("Name")
    mail_from = fields.Char("Email from")
    email_content = fields.Html("Email content")

    def create_auto_replied_record(self, data):
        email_content = "<center><table class='table table-striped'><thead><tr><th scope='col' colspan='2'><center><br/><h2 style='font-weight:bold;color:#009EE3'>Email Detail</h2><br/></center></th></tr></thead><tbody>"
        for part in data.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            try:
                # get the email body
                body = part.get_payload(decode=True).decode()
                data["Body"] = body
            except:
                pass
        for k,v in sorted(data.items()):
            email_content +="<tr><td>"+str(k)+"</td><td scope='row'>"+str(v)+"</td></tr>"

        create_id = self.sudo().create({"name":data.get("Subject",""),"mail_from":data.get("From"), "email_content":email_content})


class Shopware6PaymentMode(models.Model):
    _inherit = 'shopware6.account.payment.mode'

    @api.model
    def _get_import_rules(self):
        return [('always', 'Always'),
                ('never', 'Never'),
                ('paid', 'Paid'),
                ('authorized', 'Authorized'),
                ]

    import_rule = fields.Selection(selection='_get_import_rules',
                                   string="Import Rule",
                                   default='always',
                                   required=True)

    days_before_cancel = fields.Integer(
        string='Days before cancel',
        default=30,
        help="After 'n' days, if the 'Import Rule' is not fulfilled, the "
             "import of the sales order will be canceled.",
    )


class Shopware6Backend(models.Model):
    _inherit = 'shopware6.backend'

    export_product_prices_from_date = fields.Datetime(string='Export product prices from date')
    connector_status = fields.Boolean(string='Connector Status', default=True)
    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist', required=True)
    document_type_mapping = fields.One2many('shopware6.document.type', 'backend_id', string='Document Type mappings')
    ratepay_team_webhook_url = fields.Char('Team Webhook URL (Ratepay)',help="Here you can enter webhook url so odoo will call after ratepay delivery confirmation.")

    def synchronize_metadata(self):
        res = super(Shopware6Backend, self).synchronize_metadata()
        # We will use odoo as master for delivery time and document type so no need to import in odoo.

        for backend in self:
            for model in ['shopware6.unit']:
                self.env[model].with_delay().import_batch(backend)
        return {
            'effect': {
                'fadeout': 'slow',
                'message': _("Successfully synced <b>%s</b> with <br/><b>%s</b>.!"%(self.name,self.location)),
                'type': 'rainbow_man',
            }
        }

    def get_expired_price_product(self):
        current_time = datetime.now() + timedelta(hours=2)
        one_day_ago = datetime.now() - timedelta(days=1)
        five_day_ago = datetime.now() - timedelta(days=5)
        total_products = []
        products = self.env['product.product'].sudo().search(["&","&",("special_price","!=",False),("is_special_price_update","=",True),"|",("special_price_from","!=",False),("special_price_to","!=",False)])
        for product in products:
            special_price_from = product.special_price_from or datetime.now() - timedelta(days=1)
            special_price_to = product.special_price_to or datetime.now() + timedelta(days=1)
            if special_price_from < current_time < special_price_to:
                total_products.append(product.id)
                self._cr.execute("UPDATE product_template SET is_special_price_update='f' WHERE id=%s;"%product.product_tmpl_id.id)
        return total_products


    def export_product_prices(self):
        self.ensure_one()
        export_start_time = datetime.now()
        from_date = self.export_product_prices_from_date
        pricelist_items = self.env['product.pricelist.item'].search([['write_date', '>=', from_date]])
        product_ids = []
        if pricelist_items:
            products_to_update = pricelist_items.get_products()
            product_ids = products_to_update.ids if products_to_update else []
        _logger.info("Shopware6 EXPORT PRODUCT PRICES: found %s price list items" % (len(pricelist_items)))

        # Update based on vendor price list START

        purchase_pricelist_items = self.env['partner.pricelist.item'].search([['write_date', '>=', from_date]])
        sale_pricelist_items = self.env['partner.sale.pricelist.item'].search([['write_date', '>=', from_date]])
        partner_ids = [part.partner_id for part in purchase_pricelist_items]
        partner_ids.extend([part.partner_id for part in sale_pricelist_items])
        for partner in partner_ids:
            supplier_ids = [partner.id]+partner.child_ids.ids
            supplier_ids.extend([0,0])
            self._cr.execute("SELECT id FROM product_product WHERE product_tmpl_id IN (SELECT DISTINCT(product_tmpl_id) FROM product_supplierinfo WHERE product_tmpl_id IS NOT NULL AND name IN %s)" % str(tuple(supplier_ids)))
            temp_product_ids = [x[0] for x in self._cr.fetchall()]
            product_ids.extend(temp_product_ids)
            self._cr.execute("SELECT DISTINCT(product_id) FROM product_supplierinfo WHERE product_id IS NOT NULL AND name IN %s" % str(tuple(supplier_ids)))
            temp_product_ids = [x[0] for x in self._cr.fetchall()]
            product_ids.extend(temp_product_ids)
            #product_product = self.env["product.product"].search(['|', ('seller_ids.name', '=', partner.id), ('seller_ids.name', 'in', partner.child_ids.ids)])
            #product_ids.extend([product.id for product in product_product])
        counter = 0
        product_ids.extend(self.get_expired_price_product())
        product_ids = list(set(product_ids))
        length = len(product_ids)
        for product in product_ids:
            is_shopware6 = self.env['shopware6.product.product'].search([('openerp_id', '=', product)], limit=1)
            if is_shopware6:
                counter += 1
                try:
                    is_available = self.env['shopware6.product.update.queue'].search([('product_id', '=', product)], limit=1)
                    if is_available:
                        is_available.is_done = False
                        _logger.info("...%s product already in update queue just changed the flag."%product)
                    else:
                        self.env['shopware6.product.update.queue'].create({'product_id': product})
                        _logger.info("[%s/%s] added Product %s into the queue from vendor price list" % (counter, length, product))
                except Exception as e:
                    _logger.warn(str(e))
                    _logger.info("[%s/%s] can't add Product %s into the queue from vendor price list" % (counter, length, product))
        # Update based on vendor price list END

        self.export_product_prices_from_date = export_start_time
        self.check_shopware6_products_prices_from_queue()
        return True

    @api.model
    def check_shopware6_products_prices_from_queue(self, limit=1500, skip_price_track=False):
        products_queue = self.env['shopware6.product.update.queue'].sudo().search([('is_done', '=', False)], limit=limit)
        rec_ids = [products_queue[x:x+15] for x in range(0, len(products_queue), 15)]
        for rec in rec_ids:
            rec_id_fields = {}
            binding_rec = False
            for id in rec:
                for binding in id.product_id.shopware6_bind_ids:
                    rec_id_fields[binding.id] = ["shopware6_price_trigger"]
                    if not binding_rec:
                        binding_rec=binding
            if binding_rec and list(rec_id_fields.keys()):
                binding_rec.with_delay(priority=6,description="Mass price update for product").export_record(fields=["shopware6_price_trigger"], data_option={'rec_ids':list(rec_id_fields.keys()), "rec_id_fields":rec_id_fields})
        products_queue.is_done = True


    @api.model
    def _cron_check_price_list_item(self):
        backends = self.env['shopware6.backend'].search([])
        for backend in backends:
            backend.export_product_prices()
        return True

    @api.model
    def _cron_mass_update_product(self):
        products_queue = self.env['product.mass.update.queue'].sudo().search([('is_done', '=', False)],limit=100)
        rec_ids = [products_queue[x:x + 10] for x in range(0, len(products_queue), 10)]
        for rec in rec_ids:
            rec_id_fields = {}
            binding = False
            for id in rec:
                for binding in id.product_id.shopware6_bind_ids:
                    if binding.shopware6_id:
                        rec_id_fields[binding.id] = json.loads(id.updated_fields)
            if binding and list(rec_id_fields.keys()):
                binding.with_delay(priority=6,description="Mass update for product").export_record(fields=["shopware6_price_trigger"], data_option={'rec_ids': list(rec_id_fields.keys()), "rec_id_fields": rec_id_fields})
            rec.is_done = True