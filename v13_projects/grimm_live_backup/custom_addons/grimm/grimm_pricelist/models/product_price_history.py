# -*- coding: utf-8 -*-

import odoo.addons.decimal_precision as dp
import logging
from odoo import models, fields, api
import base64
import csv
from io import StringIO

_logger = logging.getLogger(__name__)


class ProductPriceHistory(models.Model):
    _inherit = 'product.price.history'

    sale_price = fields.Float('Sale Price', digits='Product Price')

    @api.model
    def update_products_prices(self, products, pricelist=None):
        MAX_SALE_DIFF_PLUS = float(self.env["ir.config_parameter"].get_param("price.rising.alarm.percent")) / 100
        MAX_SALE_DIFF_MINUS = float(self.env["ir.config_parameter"].get_param("price.cutting.alarm.percent")) / 100
        if not products:
            return
        if pricelist:
            products = products.with_context(
                quantity=1,
                pricelist=pricelist.id,
            )
        user = self.env['res.users'].browse(self._uid)
        self._cr.execute("""
SELECT t2.product_id, t2.cost, t2.sale_price
FROM
  (SELECT
     product_id,
     max(datetime) AS lastdt
   FROM product_price_history
   WHERE product_id = ANY (%s)
         AND company_id = %s AND transfer_on = %s
   GROUP BY product_id) AS t1
  JOIN product_price_history t2 ON t1.product_id = t2.product_id AND t1.lastdt = t2.datetime;""",
                         (products.ids, user.company_id.id, 'shopware' if self._context.get("shopware_pricelist", False) else 'magento'))
        histories = {x[0]: (x[1], x[2]) for x in self._cr.fetchall()}
        res = {}
        prescision = 2
        counter = 1
        length = len(products)

        #products_data = products.read(['standard_price', 'price', 'default_code'])
        products_data = []
        for prod in products:
            try:
                prod = prod.with_context({"uid":self._context.get("uid", self.env.user.id)})
                products_data.append({'id': prod.id, 'default_code': prod.default_code, 'standard_price': prod.calculated_standard_price, 'price': prod.calculated_magento_price, 'list_price': prod.rrp_price})
            except:
                #products_data.append({'id': prod.id, 'default_code': prod.default_code, 'standard_price': prod.calculated_standard_price, 'price': prod.calculated_magento_price, 'list_price': prod.rrp_price})
                _logger.info("Odoo not able to get price for this product ...%s" % (prod))

        _logger.info("Processing Price History for %s Products..." % (length))
        for row in products_data:
            product_id = row['id']
            new_cost = row['standard_price']
            new_sale_price = row['price']
            _logger.debug("[%s/%s] Product ID %s" % (counter, length, product_id))
            counter += 1

            prices = histories.get(product_id, None)
            try:
                old_cost, old_sale_price = round(prices[0], prescision), round(prices[1], prescision)
            except:
                old_cost, old_sale_price = 0.00, 0.00
            if old_cost != new_cost or old_sale_price != new_sale_price:
                transfer_on = 'shopware' if self._context.get("shopware_pricelist", False) else 'magento'
                # self.create({'product_id': product_id, 'cost': new_cost, 'sale_price': new_sale_price, 'transfer_on':transfer_on, 'list_price':row.get("list_price")}) Odoo13Change
                default_code = row['default_code']
                try:
                    if default_code:
                        default_code = default_code.encode('utf-8')
                except:
                    _logger.error('### Encoding Error %s', default_code)
                vals = {'standard_price': new_cost, 'list_price': new_sale_price, 'default_code': default_code}
                if old_sale_price:
                    sale_price_diff = round((new_sale_price - old_sale_price) / old_sale_price, 2)
                    if (sale_price_diff > 0 and sale_price_diff > MAX_SALE_DIFF_PLUS) or (
                            sale_price_diff < 0 and abs(sale_price_diff) > MAX_SALE_DIFF_MINUS):
                        vals['diff'] = sale_price_diff
                else:
                    vals['diff'] = 1
                res[product_id] = vals
        # if res and len(res) > 0:
        #     self.send_alarm_email(res, counter)
        return res
        # return self.env['product.product'].browse(res)

    @api.model
    def send_alarm_email(self, products, counter=0):
        if self.env["ir.config_parameter"].get_param("price.alarm.emails", default=False):
            data = [['ID', 'Article Number', 'Sale Price', 'Different'], ]
            extend_data = [[key, value['default_code'], str(value['list_price']).replace('.', ','),
                            str(value['diff']).replace('.', ',')] for key, value in products.items() if
                           'diff' in value]
            vals = {'email_from': 'office@grimm-gastrobedarf.de',
                    'email_to': self.env["ir.config_parameter"].get_param("price.alarm.emails"),
                    'body_html': "<pre>Hallo liebe Kollegen,<br /><br />gerade wurde eine Preis-Aktualisierung ausgef&uuml;hrt. "
                                 "{} Produkte wurden gepr&uuml;ft. {} davon haben neuen Preis.<br /><br />Beste Gr&uuml;&szlig;e<br />"
                                 "Odoo Preis Updater</pre>".format(
                        counter, len(extend_data)), 'message_type': 'email',
                    'subject': 'Preis Überwachung: Alarm'}
            mail = self.env['mail.mail'].create(vals)

            if extend_data:
                data.extend(extend_data)
                f = StringIO()
                csv.writer(f, delimiter=';').writerows(data)
                datas = base64.b64encode(f.getvalue().encode('utf-8'))
                attachment = self.env['ir.attachment'].create(
                    {'name': 'price_alarm', 'type': 'binary', 'datas': datas})
                mail.attachment_ids = [(4, attachment.id)]

            mail.send()

    def recalculate(self):
        LIMIT = 1000
        all_products = self.env['product.product'].search(
            ['|', ('magento_pp_bind_ids', '!=', False), ('magento_ptmpl_bind_ids', '!=', False)])
        page = 0
        products = all_products[page * LIMIT:(page + 1) * LIMIT]
        while products:
            self.update_products_prices(products)
            page += 1
            products = all_products[page * LIMIT:(page + 1) * LIMIT]

    @api.model
    def check_products_prices_from_queue(self, limit=1000, skip_price_track = False):
        products_queue = self.env['product.update.queue'].search([], limit=limit)
        product_ids = [product.product_id.id for product in products_queue]
        products = self.env['product.product'].browse(product_ids)
        product_tmpl_ids = list(set([product.product_tmpl_id.id for product in products]))
        if not skip_price_track:
            res = products.update_price_history()
            if res:
                _logger.info("%s Products to update to Magento", len(res))
                products = self.env['product.product'].browse(list(res.keys()))
                product_tmpl_ids = [product.product_tmpl_id.id for product in products]
                product_tmpl_ids = set(product_tmpl_ids)
        self.env['product.template'].browse(product_tmpl_ids).with_context(
            {'no_trigger_price_again': True}).write(
            {'update_prices_trigger': True})

        products_queue.unlink()