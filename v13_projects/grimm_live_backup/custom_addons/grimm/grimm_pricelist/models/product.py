# -*- coding: utf-8 -*-


import logging

from odoo import models, fields, tools, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import MissingError
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

SPECIAL_PURCHASE_PRICE_EXPIRED_INTERVAL_DAYS = 1

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    price_calculation_group = fields.Many2one("product.price.group", string="Price Calculation Group",
                                              copy=True, related="product_variant_ids.price_calculation_group",
                                              inverse='_set_product_product_related_fields', track_visibility='onchange', readonly=False)
    price_on_request = fields.Boolean(string="Price on request", copy=True,
                                      related="product_variant_ids.price_on_request",
                                      help="Set Purchase Price & Sale Price = 9999,99")
    price_up_to_date = fields.Boolean(string='Price up to date',
                                      help="A price's status indicates special situations affecting it:\n"
                                           " * False indicates the prices need to be recalculated. It is the default state\n"
                                           " * True indicates the prices are already calculated.\n",
                                      required=True, copy=False, default='blocked', readonly=True,
                                      related='product_variant_ids.price_up_to_date',
                                      store=True)
    cost_price = fields.Monetary(string='Cost Price', help='Cost Price will be calculated from price calculation',
                                 related='product_variant_ids.cost_price', copy=False)

    # Special Purchase Price
    special_purchase_price = fields.Monetary(string='Special Purchase Price', digits='Product Price',
                                             copy=True, help='The special price for purchase.',
                                             related='product_variant_ids.special_purchase_price', track_visibility='onchange', readonly=False)
    special_purchase_price_from = fields.Date(string='Special Purchase Price from', copy=True,
                                              related='product_variant_ids.special_purchase_price_from', readonly=False)
    special_purchase_price_to = fields.Date(string='Special Purchase Price to', copy=True,
                                            related='product_variant_ids.special_purchase_price_to', readonly=False)
    is_special_purchase_price_expired = fields.Boolean(String='Is Special Purchase Price expired?',
                                                       related='product_variant_ids.is_special_purchase_price_expired', readonly=False)
    calculated_standard_price = fields.Float(string='Calculated Purchase Price',
                                             compute='_compute_calculated_standard_price', store=False)
    name = fields.Char('Name', required=True, track_visibility='onchange')

    @api.depends('seller_ids')
    def _compute_calculated_standard_price(self):
        for product in self:
            if product.product_variant_count > 1:
                product.calculated_standard_price = 0
            else:
                try:
                    product.calculated_standard_price = product.product_variant_id.calculated_standard_price
                except:
                    product.calculated_standard_price = product.product_variant_id.calculated_standard_price


    def _set_product_product_related_fields(self):
        for product_template in self:
            if len(product_template.product_variant_ids) == 1:
                product_template.product_variant_ids.price_calculation_group = product_template.price_calculation_group.id
                product_template.product_variant_ids.price_on_request = product_template.price_on_request


class ProductProduct(models.Model):
    _inherit = 'product.product'
    PRICE_HISTORY_FIELDS = ['standard_price', 'price', 'list_price', 'lst_price', 'rrp_price',
                            'price_calculation_group', 'seller_ids', 'special_purchase_price',
                            'special_purchase_price_from', 'special_purchase_price_to']

    standard_price = fields.Float(string='Purchase Price', compute='_compute_standard_price', store=False,
                                  company_dependent=False)
    calculated_standard_price = fields.Float(string='Calculated Purchase Price',
                                             compute='_compute_calculated_standard_price', store=False,
                                             company_dependent=False)
    price_calculation_group = fields.Many2one("product.price.group", string="Price Calculation Group", copy=True)

    product_update_queue_id = fields.One2many(comodel_name="product.update.queue", inverse_name="product_id")
    price_on_request = fields.Boolean(string="Price on request", copy=True,
                                      help="Set Purchase Price & Sale Price = 9999,99")
    cost_price = fields.Monetary(string='Cost Price', help='Cost Price will be calculated from price calculation',
                                 copy=False)
    price_up_to_date = fields.Boolean(
        string='Price up to date',
        track_visibility='onchange',
        help="A price's status indicates special situations affecting it:\n"
             " * False indicates the prices need to be recalculated. It is the default state\n"
             " * True indicates the prices are already calculated.\n",
        required=True, copy=False, default=False, readonly=True)

    # Special Purchase Price
    special_purchase_price = fields.Monetary(string='Special Purchase Price', digits='Product Price',
                                             copy=True, help='The special price for purchase.')
    special_purchase_price_from = fields.Date(string='Special Purchase Price from', copy=True)
    special_purchase_price_to = fields.Date(string='Special Purchase Price to', copy=True)
    is_special_purchase_price_expired = fields.Boolean(String='Is Special Purchase Price expired?',
                                                       compute='compute_special_purchase_price_expired')

    def compute_special_purchase_price_expired(self):
        """
        compute if product special purchase price is expired
        :return: None
        """
        for product in self:
            if product.special_purchase_price_from and product.special_purchase_price_to:
                current_datetime = fields.Datetime.now().date()
                if current_datetime >= product.special_purchase_price_from and current_datetime <= product.special_purchase_price_to:
                    product.is_special_purchase_price_expired = False
                else:
                    product.is_special_purchase_price_expired = True
            else:
                product.is_special_purchase_price_expired = True

    @api.model
    def get_special_purchase_price(self):
        """
        return special purchase price for this time.
        None for expired or time is not valid
        :return: valid special purchase price, None for invalid
        """
        if not self:
            return None
        if not self.is_special_purchase_price_expired:
            return self.special_purchase_price
        return None

    @api.model
    def get_product_expired_special_purchase_price(self):
        """
        get the products with the expired purchase price
        :return:
        """
        expired_datetime = datetime.now() - timedelta(days=SPECIAL_PURCHASE_PRICE_EXPIRED_INTERVAL_DAYS)
        products = self.env['product.product'].sudo().search(
            [('special_purchase_price_to', '>=', expired_datetime.strftime(DEFAULT_SERVER_DATE_FORMAT))])
        return products

    def _is_valid_pricelist(self, rule):
        if rule.attribute_set_id and rule.attribute_set_id != self.attribute_set_id:
            return False
        if rule.product_name and rule.product_name.lower() not in self.with_context(
                lang='de_DE').display_name.lower() and rule.product_name.lower() not in self.with_context(
                lang='EN').display_name.lower():
            return False
        if rule.product_net_weight > self.net_weight:
            return False
        if rule.product_gross_weight > self.weight:
            return False
        if rule.product_brand_id and rule.product_brand_id.id != self.product_tmpl_id.product_brand_id.id:
            return False
        if rule.min_uvp and self.rrp_price < rule.min_uvp:
            return False
        if rule.price_calculation_group and rule.price_calculation_group != self.price_calculation_group:
            return False
        if rule.date_start or rule.date_end:
            date = (datetime.strptime(str(self._context.get('date').date() if self._context.get('date', False) else fields.Date.context_today(self)),'%Y-%m-%d'))
            date_start = (datetime.strptime(str(rule.date_start if rule.date_start else (date - timedelta(days=2)).date()),'%Y-%m-%d'))
            date_end = (datetime.strptime(str(rule.date_end if rule.date_end else (date + timedelta(days=2)).date()),'%Y-%m-%d'))
            if not (date_start <= date <= date_end):
                return False

        if rule.product_id and self.id != rule.product_id.id:
            return False

        if rule.categ_id:
            cat = self.categ_id
            while cat:
                if cat.id == rule.categ_id.id:
                    break
                cat = cat.parent_id
            if not cat:
                return False
        if rule.is_advance_domain:
            import ast
            domain = ast.literal_eval(rule.advance_domain)
            if domain:
                product_product = self.env['product.product'].sudo().search(domain)
                prod_ids = [prod.id for prod in product_product]
                if self.id not in prod_ids:
                    return False
        return True

    def _check_to_compare_date(self):
        return True # We need to check with current date every time.
        if self._context.get("params", False):
            if self._context.get("params").get("model", "") in ["sale.order", "purchase.order", "account.move"]:
                return False
        return True

    def _get_extra_price(self, partner,supplier_standard_price, price_type):
        while partner.parent_id:
            partner = partner.parent_id
        price_trackings = []
        pricelist_ids = partner.sale_pricelist_ids if price_type == 'out' else partner.purchase_pricelist_ids
        if pricelist_ids:
            base_price = supplier_standard_price
            for rule in pricelist_ids:
                price_info = [rule,base_price]
                if rule.attribute_set_id and rule.attribute_set_id != self.attribute_set_id:
                    continue
                if rule.product_name and rule.product_name.lower() not in self.with_context(lang='de_DE').display_name.lower() and rule.product_name.lower() not in self.with_context(lang='EN').display_name.lower():
                    continue
                if rule.product_net_weight > self.net_weight:
                    continue
                if rule.product_gross_weight > self.weight:
                    continue
                if rule.product_brand_id and rule.product_brand_id.id != self.product_tmpl_id.product_brand_id.id:
                    continue
                if rule.min_uvp and self.rrp_price < rule.min_uvp:
                    continue
                if rule.price_calculation_group and rule.price_calculation_group != self.price_calculation_group:
                    continue
                if self._check_to_compare_date():
                    if rule.date_start or rule.date_end:
                        #date = (datetime.strptime(str(self._context.get('date').date() if self._context.get('date', False) else fields.Date.context_today(self)), '%Y-%m-%d'))
                        date = (datetime.strptime(str(fields.Date.context_today(self)), '%Y-%m-%d')) # Removed checking date from context. Only check with current date.
                        date_start = (datetime.strptime(str(rule.date_start if rule.date_start else (date - timedelta(days=2)).date()), '%Y-%m-%d'))
                        date_end = (datetime.strptime(str(rule.date_end if rule.date_end else (date + timedelta(days=2)).date()), '%Y-%m-%d'))
                        if not (date_start <= date <= date_end):
                            continue
                if (rule.is_accessory_part == 'y' and not self.is_accessory_part) or (rule.is_accessory_part == 'n' and self.is_accessory_part):
                    continue

                if (rule.is_spare_part == 'y' and not self.is_spare_part) or (rule.is_spare_part == 'n' and self.is_spare_part):
                    continue

                if (rule.is_device == 'y' and not self.is_device) or (rule.is_device == 'n' and self.is_device):
                    continue
                if (rule.is_product_pack == 'y' and not self.is_pack) or (rule.is_product_pack == 'n' and self.is_pack):
                    continue

                if rule.product_id and self.id != rule.product_id.id:
                    continue

                if rule.categ_id:
                    cat = self.categ_id
                    while cat:
                        if cat.id == rule.categ_id.id:
                            break
                        cat = cat.parent_id
                    if not cat:
                        continue
                qty_uom_id = self._context.get('uom') or self.uom_id.id
                price_uom = self.env['uom.uom'].browse([qty_uom_id])
                convert_to_price_uom = (lambda price: self.uom_id._compute_price(price, price_uom))

                if rule.is_advance_domain:
                    import ast
                    domain = ast.literal_eval(rule.advance_domain)
                    if domain:
                        product_product = self.sudo().filtered_domain(domain)
                        prod_ids = [prod.id for prod in product_product]
                        if self.id not in prod_ids:
                            continue
                if base_price is not False:
                    if rule.compute_price == 'fixed':
                        price_info.append(u"%s + %s %s" % (round(base_price,2), rule.fixed_price, rule.currency_id.symbol))
                        base_price = base_price + rule.fixed_price
                        price_info.append(base_price)
                    elif rule.compute_price == 'percentage':
                        price_info.append(u"%s%s - %s%%" % (round(base_price,2), rule.currency_id.symbol, rule.percent_price))
                        base_price = (base_price - (base_price * (rule.percent_price / 100))) or 0.0
                        price_info.append(base_price)
                    else:
                        # complete formula
                        price_limit = base_price
                        discount = (base_price * (rule.price_discount / 100))
                        price_msg = u"%s %s %s%%" % (round(base_price,2), rule.percent_sign, rule.price_discount)
                        if rule.percent_sign == '+':
                            base_price = (base_price + discount) or 0.0
                        else:
                            base_price = (base_price - discount) or 0.0

                        if rule.price_round:
                            base_price = tools.float_round(base_price, precision_rounding=rule.price_round)
                            price_msg = u"round(%s, rule.price_round)" % price_msg

                        if rule.price_surcharge:
                            price_surcharge = convert_to_price_uom(rule.price_surcharge)
                            price_msg = u"%s + %s%s" % (price_msg, price_surcharge, rule.currency_id.symbol)
                            base_price += price_surcharge

                        if rule.price_min_margin:
                            price_min_margin = convert_to_price_uom(rule.price_min_margin)
                            base_price = max(base_price, price_limit + price_min_margin)
                            price_msg = u"max(%s, %s)" % (price_msg, price_limit + price_min_margin)

                        if rule.price_max_margin:
                            price_max_margin = convert_to_price_uom(rule.price_max_margin)
                            base_price = min(base_price, price_limit + price_max_margin)
                            price_msg = u"min(%s, %s)" % (price_msg, price_limit + price_max_margin)
                        price_info.append(price_msg)
                        price_info.append(base_price)
                price_trackings.append(price_info)
            supplier_standard_price = base_price
        return {'price':supplier_standard_price,'price_msg':price_trackings}

    def _get_session_user(self):
        '''
        Created method to fetch correct price for multi company issue.
        Based on return user odoo will perform price calculation.
        :return user object:
        '''
        shopware_user = self.env["res.users"].search([('login', '=', 'shopware@grimm-gastrobedarf.de')],limit=1)
        magento_user = self.env["res.users"].search([('login', '=', 'magento@grimm-gastrobedarf.de')], limit=1)

        job_uuid = self._context.get("job_uuid", False)
        if job_uuid:
            queue_job = self.env['queue.job'].search([('uuid', '=', job_uuid)], limit=1)
            if queue_job and queue_job.channel == 'root.magento':
                return magento_user
            if queue_job and queue_job.channel == 'root.shopware':
                return shopware_user

        if self._context.get("company_id", False):
            return shopware_user if self._context.get("company_id",False) == 3 else magento_user
        else:
            return shopware_user if self.env.company.id == 3 else magento_user
        return self.env["res.users"].browse(self._context.get("uid", self.env.user.id))

    def _get_purchase_price(self):
        self.ensure_one()

        current_user = self._get_session_user()
        special_purchase_price = self.get_special_purchase_price()

        if special_purchase_price is not None: # If product has special price don't care about any other rules, just return special purchase price
            return special_purchase_price

        seller = self.with_context({'product_id': self.id, 'force_company': current_user.company_id.id})._select_seller()
        if not seller: # If there is no seller then return list price
            return self.rrp_price

        parent_seller = seller.name
        while parent_seller.parent_id:
            parent_seller = parent_seller.parent_id
        override_price = True if parent_seller.apply_purchase_pricelist else False


        if getattr(self, "is_pack", False) and getattr(self, "cal_pack_price", False):
            final_price = 0
            for pack_prod in self.pack_ids:
                final_price += pack_prod.product_id._get_purchase_price() * pack_prod.qty_uom
            #if override_price:
            #    final_price = self._get_extra_price(seller.name, final_price, 'in').get("price")
        else:
            if override_price:
                final_price = self._origin._get_extra_price(seller.name, self.rrp_price, 'in').get("price") # We have used self._origin instead of self due to "Database fetch misses ids ({}) and has extra ids ({}), may be caused by a type incoherence in a previous request" error
            else:
                final_price = seller.price
        return final_price

    @api.depends('seller_ids')
    def _compute_calculated_standard_price(self):

        for product in self:
            product.calculated_standard_price = product._get_purchase_price()


        # for product in self:
        #     final_price = 0
        #     pass_pack_price = False
        #     current_user = self.env["res.users"].browse(self._context.get("uid", self.env.user.id))
        #     seller = product.with_context({'product_id': product.id,
        #                                    'force_company': current_user.company_id.id})._select_seller()
        #     special_purchase_price = product.get_special_purchase_price()
        #     parent_seller = seller.name
        #     override_price = False
        #     while parent_seller.parent_id:
        #         parent_seller = parent_seller.parent_id
        #     override_price = True if parent_seller.apply_purchase_pricelist else False  # self.env["ir.config_parameter"].sudo().get_param("apply_partner_pricelist", default='False') == 'True' else False
        #
        #     if getattr(product, "is_pack", False) and getattr(product, "cal_pack_price", False):
        #         for pack_prod in product.pack_ids:
        #             # try:
        #             #     final_price += pack_prod.product_id.calculated_standard_price * pack_prod.qty_uom  # purchase_price.price * pack_prod.qty_uom
        #             # except:
        #             #     final_price += pack_prod.product_id.calculated_standard_price * pack_prod.qty_uom  # purchase_price.price * pack_prod.qty_uom
        #             special_purchase_price = pack_prod.product_id.get_special_purchase_price()
        #
        #             pack_seller = pack_prod.product_id.with_context(
        #                 {'product_id': pack_prod.product_id.id,
        #                  'force_company': current_user.company_id.id})._select_seller()
        #             pack_parent_seller = pack_seller.name
        #             while pack_parent_seller.parent_id:
        #                 pack_parent_seller = pack_parent_seller.parent_id
        #             pack_override_price = True if pack_parent_seller.apply_purchase_pricelist else False
        #
        #             if special_purchase_price is not None:
        #                 final_price +=  special_purchase_price
        #             elif pack_override_price:
        #                 final_price += pack_prod.product_id._get_extra_price(pack_parent_seller, pack_prod.product_id.rrp_price, 'in').get("price") * pack_prod.qty_uom
        #             else:
        #                 final_price += pack_seller.price * pack_prod.qty_uom
        #         if override_price:
        #             final_price = product._get_extra_price(seller.name, final_price, 'in').get("price")
        #
        #     else:
        #         if not seller:
        #             _logger.warning("[Price Calculation]: Product has no supplier" + str(product) + str(self.env.user))
        #             product.calculated_standard_price = product.rrp_price
        #             continue
        #         # seller = seller.with_context({'product_id': product.id, 'no_special_purchase_price': True, 'force_company':self.env.user_id.company_id.id})
        #
        #         if special_purchase_price is not None:
        #             final_price += special_purchase_price
        #         elif override_price:
        #             final_price = product._get_extra_price(seller.name,
        #                                                    final_price if pass_pack_price else product.rrp_price,
        #                                                    'in').get("price")
        #         else:
        #             final_price = seller.price
        #
        #     product.calculated_standard_price = final_price

    @api.depends('seller_ids')
    def _compute_standard_price(self):
        for product in self:
            special_purchase_price = product.get_special_purchase_price()
            try:  # TODO had to add try except because odoo was facing key error issue.
                product.standard_price = special_purchase_price if special_purchase_price is not None else product.calculated_standard_price
            except:
                product.standard_price = special_purchase_price if special_purchase_price is not None else product.calculated_standard_price

    def set_price_from_price_list(self, field_name, price_list=None, partner=False, quantity=1.0):
        """
        Set the calculated price from price list on a product field
        :param field_name: field to set the new price
        :param price_list: Price List for price calculation
        :param partner: Who buy these products
        :param quantity: sold quantity of each product
        :return: None
        """
        prices = self.compute_price_from_price_list(price_list=price_list, partner=partner, quantity=quantity)
        for product in self:
            setattr(product, field_name, prices.get(product.id, 0.0))

    def compute_price_from_price_list(self, price_list=None, partner=False, quantity=1.0):
        """
        Compute the prices with price list and return it
        :param price_list: Price List for price calculation
        :param partner: Who buy these products
        :param quantity: sold quantity of each product
        :return: dict of product id and price
        :rtype: dict
        """
        prices = {}
        if price_list:
            product_quantity_partner_list = [(x, quantity, partner) for x in self]
            prices = price_list._price_get_multi(product_quantity_partner_list)
        return prices

    @api.model
    def check_products_prices(self, limit=1000):
        products = self.env['product.product'].search([('price_up_to_date', '=', False)], limit=limit)
        products.calculate_product_prices()
        products.set_price_up_to_date()

    def calculate_product_prices(self):
        self.compute_cost_price()

    def compute_cost_price(self):
        cost_price_list = self.env["ir.config_parameter"].sudo().get_param("cost.price.list", default=None)
        if not cost_price_list:
            raise MissingError(_('No price list for cost price is configured.'))
        cost_price_list = self.env['product.pricelist'].browse(int(cost_price_list))
        for product in self:
            product = product.with_context(
                quantity=1,
                pricelist=cost_price_list.id,
                standard_price=product.rrp_price,
                currency_id=product.currency_id.id
            )
            cost_price_extra = product.price
            # standard_price = product.standard_price
            # cost_price = standard_price + cost_price_extra
            cost_price = cost_price_extra
            product.cost_price = cost_price

    def compute_purchase_price(self):
        pass

    def clear_price_up_to_date(self):
        res = self.write({'price_up_to_date': False})
        return res

    def set_price_up_to_date(self):
        res = self.write({'price_up_to_date': True})
        return res

    def update_price_history(self, pricelist=None):
        context_dict = {"shopware_pricelist":self._context.get("shopware_pricelist", False),'uid':self._context.get("uid", self.env.user.id)}
        if self._context.get("shopware_pricelist", False):
            pricelist = self._context.get("shopware_pricelist", False)
        else:
            magento_user = self.env["res.users"].sudo().search([['login', '=', 'magento@grimm-gastrobedarf.de']])
            if magento_user:
                context_dict["uid"] = magento_user.id

        res = self.env['product.price.history'].with_context(context_dict).update_products_prices(self, pricelist=pricelist)
        # product_tmpl_ids = [product.product_tmpl_id.id for product in res]
        # self.env['product.template'].browse(product_tmpl_ids).write({})

        return res

    def write(self, vals):
        res = super(ProductProduct, self).write(vals)
        no_trigger_price_again = self._context.get('no_trigger_price_again', None)
        if not no_trigger_price_again and any([field for field in self.PRICE_HISTORY_FIELDS if field in vals]):
            for product in self:
                try:
                    if not self.env['product.update.queue'].search([('product_id', '=', product.id)]):
                        self.env['product.update.queue'].create({'product_id': product.id})
                except:
                    pass
        return res

    @api.model
    def create(self, vals):
        res = super(ProductProduct, self).create(vals)
        no_trigger_price_again = self._context.get('no_trigger_price_again', None)
        if not no_trigger_price_again and any([field for field in self.PRICE_HISTORY_FIELDS if field in vals]):
            res.update_price_history()
        return res

    def _set_standard_price(self, value):
        """
        do nothing more
        :param cr:
        :param uid:
        :param product_id:
        :param value:
        :param context:
        :return:
        """
        pass


class ProductSupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    price = fields.Float(compute='_compute_price')
    rrp_price = fields.Float(string='RRP Price', required=True, digits='Product Price',
                             help="Recommended Retail Price from Supplier", default=0)
    product_id = fields.Many2one('product.product', copy=False)

    @api.depends('rrp_price')
    def _compute_price(self):
        product_obj = self.env['product.product']
        product = None

        if self._context:
            product_id = self._context.get('product_id', None)
            no_special_purchase_price = self._context.get('no_special_purchase_price', None)
            if product_id:
                product = product_obj.browse(product_id)
        else:
            no_special_purchase_price = None

        for record in self:
            if not product:
                product = record.product_id
                if record.product_tmpl_id:
                    product = product_obj.search([('product_tmpl_id', '=', record.product_tmpl_id.id)], limit=1)

            if not product:
                _logger.warning('No Product is linked with this Supplier!')

            supplier_pricelist = record.name.get_supplier_pricelist()
            price = record.rrp_price
            if product:
                special_purchase_price = product.get_special_purchase_price()
                # Commented below code related to OD-822
                #if product.price_on_request:
                #    price = 9999.99
                if special_purchase_price is not None and not no_special_purchase_price:
                    price = special_purchase_price
                elif supplier_pricelist:
                    supplier, pricelist = supplier_pricelist
                    product = record.product_id if record.product_id else product # Added this code to resolve OD-775
                    product = product.with_context(
                        quantity=1,
                        pricelist=pricelist.id,
                        standard_price=record.rrp_price,
                        supplier_id=supplier.id,
                        currency_id=record.currency_id.id
                    )
                    price = product.price
                if price == 0:
                    price = product.rrp_price
                #if not price:
                #    price = product.rrp_price
            parent_seller = record.name
            while parent_seller.parent_id:
                parent_seller = parent_seller.parent_id
            if parent_seller.apply_purchase_pricelist:
                price = product.calculated_standard_price

            record.price = price
