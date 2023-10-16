# -*- coding: utf-8 -*-

import logging
import time
from itertools import chain

from odoo import models, fields, tools, api, _
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, pycompat
from odoo.tools import float_repr

_logger = logging.getLogger(__name__)

SPECIAL_PURCHASE_PRICE_INTERVAL_DAYS = 2


class Pricelist(models.Model):
    _inherit = 'product.pricelist'

    supplier_ids = fields.One2many(comodel_name='res.partner', string='Suppliers',
                                   inverse_name='property_supplier_pricelist',
                                   help='Price list to calculate the purchase price',
                                   domain=[('supplier_rank', '>', 0)],
                                   track_visibility='onchange')
    customer_ids = fields.One2many(comodel_name='res.partner', string='Customers',
                                   inverse_name='property_product_pricelist',
                                   help='Price list to calculate the sale price',
                                   domain=[('customer_rank', '>', 0)],
                                   track_visibility='onchange')

    def name_get(self):
        result = []
        for pl in self:
            name = pl.name + ' (' + pl.currency_id.name + ')'
            result.append((pl.id, name))
        return result

    def _compute_price_rule(self, products_qty_partner, date=False, uom_id=False, price_track = [], flush=False):
        """ Low-level method - Mono pricelist, multi products
        Returns: dict{product_id: (price, suitable_rule) for the given pricelist}

        If date in context: Date of the pricelist (%Y-%m-%d)

            :param products_qty_partner: list of typles products, quantity, partner
            :param datetime date: validity date
            :param ID uom_id: intermediate unit of measure
        """
        self.ensure_one()
        if flush: # Added to flush price tracking old data.
            price_track = []
        current_user = self.env["res.users"].browse(self._context.get("uid", self.env.user.id))
        if not date:
            date = self._context.get('date') or fields.Date.context_today(self)
        if not uom_id and self._context.get('uom'):
            uom_id = self._context['uom']
        if uom_id:
            # rebrowse with uom if given
            products = [item[0].with_context(uom=uom_id) for item in products_qty_partner]
            products_qty_partner = [(products[index], data_struct[1], data_struct[2]) for index, data_struct in
                                    enumerate(products_qty_partner)]
        else:
            products = [item[0] for item in products_qty_partner]

        if not products:
            return {}

        categ_ids = {}
        # grimm_pricelist
        supplier_id = self._context.get('supplier_id', None)
        standard_price = self._context.get('standard_price', None)
        supplier_ids = {}
        brand_ids = {}
        price_calculation_groups = {}
        attribute_set_ids = {}
        # grimm_pricelist
        for p in products:
            # Category
            categ = p.categ_id
            while categ:
                categ_ids[categ.id] = True
                categ = categ.parent_id
            # Seller/Supplier
            seller = False
            if p._name == "product.template":
                p = p.product_variant_id
            seller = p.with_context({'product_id': p.id, 'no_special_purchase_price': True, 'force_company': self._context.get('force_company',current_user.company_id.id)})._select_seller()
            if seller:
                supplier = seller.name
                while supplier:
                    supplier_ids[supplier.id] = True
                    supplier = supplier.parent_id
            # Product brand
            if p.product_tmpl_id.product_brand_id:
                brand_ids[p.product_tmpl_id.product_brand_id.id] = True
            # Price calculation group
            if p.price_calculation_group:
                price_calculation_groups[p.price_calculation_group.id] = True
            # Attribute Set
            if p.attribute_set_id:
                attribute_set_ids[p.attribute_set_id.id] = True
        categ_ids = list(categ_ids)
        supplier_ids = list(supplier_ids)
        brand_ids = list(brand_ids)
        price_calculation_groups = list(price_calculation_groups)
        attribute_set_ids = list(attribute_set_ids)

        is_product_template = products[0]._name == "product.template"
        if is_product_template:
            prod_tmpl_ids = [tmpl.id for tmpl in products]
            # all variants of all products
            prod_ids = [p.id for p in
                        list(chain.from_iterable([t.product_variant_ids for t in products]))]
        else:
            prod_ids = [product.id for product in products]
            prod_tmpl_ids = [product.product_tmpl_id.id for product in products]

        # Load all rules
        self._cr.execute(
            'SELECT item.id '
            'FROM product_pricelist_item AS item '
            'LEFT JOIN product_category AS categ '
            'ON item.categ_id = categ.id '
            'WHERE (item.product_tmpl_id IS NULL OR item.product_tmpl_id = ANY(%s))'
            'AND (item.product_id IS NULL OR item.product_id = ANY(%s))'
            'AND (item.categ_id IS NULL OR item.categ_id = ANY(%s)) '
            'AND (item.pricelist_id = %s) '
            'AND (item.date_start IS NULL OR item.date_start<=%s) '
            'AND (item.date_end IS NULL OR item.date_end>=%s)'
            'AND (item.apply_supplier_id IS NULL OR item.apply_supplier_id = ANY(%s)) '
            'AND (item.product_brand_id IS NULL OR item.product_brand_id = ANY(%s)) '
            'AND (item.price_calculation_group IS NULL OR item.price_calculation_group = ANY(%s)) '
            'AND (item.attribute_set_id IS NULL OR item.attribute_set_id = ANY(%s)) '
            'ORDER BY item.apply_supplier_id, item.applied_on, item.attribute_set_id, item.price_calculation_group, item.product_brand_id, item.product_name, item.min_uvp DESC,  item.min_quantity DESC',
            (prod_tmpl_ids, prod_ids, categ_ids, self.id, date, date, supplier_ids, brand_ids, price_calculation_groups,
             attribute_set_ids,)) # Removed parent_left because odoo13 removed from product category

        item_ids = [x[0] for x in self._cr.fetchall()]
        items = self.env['product.pricelist.item'].browse(item_ids)
        results = {}
        for product, qty, partner in products_qty_partner:
            results[product.id] = 0.0
            suitable_rule = False

            # added for grimm # Commented below code related to OD-822
            #if product.price_on_request:
            #    results[product.id] = (9999.99, False, _("Price on request: 9999,99"))
            #    continue
            # seller = product._select_seller()
            if product._name == "product.template":
                product = product.product_variant_id
            seller = product.with_context({'product_id': product.id, 'no_special_purchase_price': True, 'force_company': self._context.get('force_company',current_user.company_id.id)})._select_seller()
            if product.price_calculation_group:
                items_by_group = [item for item in items if
                                  item.price_calculation_group == product.price_calculation_group]
                items_by_group.extend(
                    [item for item in items if item.price_calculation_group != product.price_calculation_group])
            else:
                items_by_group = items
            if seller:
                items_by_seller = [item for item in items_by_group if item.apply_supplier_id.id == seller.name.id]
                items_by_seller.extend([item for item in items_by_group if item.apply_supplier_id.id != seller.name.id])
            else:
                items_by_seller = items_by_group
            # added for grimm

            # Final unit price is computed according to `qty` in the `qty_uom_id` UoM.
            # An intermediary unit price may be computed according to a different UoM, in
            # which case the price_uom_id contains that UoM.
            # The final price will be converted to match `qty_uom_id`.
            qty_uom_id = self._context.get('uom') or product.uom_id.id
            price_uom_id = product.uom_id.id
            price_tracking = u""  # Grimm
            qty_in_product_uom = qty
            if qty_uom_id != product.uom_id.id:
                try:
                    qty_in_product_uom = self.env['uom.uom'].browse([self._context['uom']])._compute_quantity(qty,
                                                                                                                  product.uom_id)
                except UserError:
                    # Ignored - incompatible UoM in context, use default product UoM
                    pass

            # if Public user try to access standard price from website sale, need to call price_compute.
            # TDE SURPRISE: product can actually be a template
            price = product.price_compute('list_price')[product.id]

            price_uom = self.env['uom.uom'].browse([qty_uom_id]) #Odoo13 changed product.uom to uom.uom
            base_price = False
            for rule in items_by_seller:
                price_tracking = u""  # Grimm
                if rule.min_quantity and qty_in_product_uom < rule.min_quantity:
                    continue
                # GRIMM
                if rule.attribute_set_id and rule.attribute_set_id != product.attribute_set_id:
                    continue
                if rule.product_name and rule.product_name.lower() not in product.with_context(lang='de_DE').display_name.lower() and rule.product_name.lower() not in product.with_context(lang='EN').display_name.lower():
                    continue
                #if rule.product_net_weight > product.net_weight: #Odoo13Change
                #    continue
                if rule.product_gross_weight > product.weight:
                    continue
                if rule.product_brand_id and rule.product_brand_id.id != product.product_tmpl_id.product_brand_id.id:
                    continue
                if rule.min_uvp and product.rrp_price < rule.min_uvp:
                    continue
                if rule.price_calculation_group and rule.price_calculation_group != product.price_calculation_group:
                    continue
                if is_product_template:
                    if rule.product_tmpl_id and product.id != rule.product_tmpl_id.id:
                        continue
                    if rule.product_id and not (
                            product.product_variant_count == 1 and product.product_variant_id.id == rule.product_id.id):
                        # product rule acceptable on template if has only one variant
                        continue
                else:
                    if rule.product_tmpl_id and product.product_tmpl_id.id != rule.product_tmpl_id.id:
                        continue
                    if rule.product_id and product.id != rule.product_id.id:
                        continue

                if rule.categ_id:
                    cat = product.categ_id
                    while cat:
                        if cat.id == rule.categ_id.id:
                            break
                        cat = cat.parent_id
                    if not cat:
                        continue
                # Grimm
                if supplier_id and rule.base == 'standard_price' and standard_price is not None:
                    price = rule.base_pricelist_id.currency_id.compute(standard_price, self.currency_id, round=False)
                    base_price = price
                elif rule.base == 'pricelist' and rule.base_pricelist_id:
                    price_tmp = rule.base_pricelist_id.with_context(track = self._context.get("track", False))._compute_price_rule([(product, qty, partner)], price_track=price_track)[
                        product.id]  # TDE: 0 = price, 1 = rule
                    price_tracking = price_tmp[2]
                    price_tmp = price_tmp[0]
                    price = rule.base_pricelist_id.currency_id.compute(price_tmp, self.currency_id, round=False)
                    base_price = price
                else:
                    # if base option is public price take sale price else cost price of product
                    # price_compute returns the price in the context UoM, i.e. qty_uom_id
                    #_logger.info("Supplier ID is ==> "+str(supplier_id)+" and standard price is ===> "+str(standard_price))
                    #_logger.info("Calling method for product ==> "+str(product)+" with rule ==> "+str(rule)+str(rule.base))
                    price = product.price_compute(rule.base)[product.id]
                    base_price = price

                convert_to_price_uom = (lambda price: product.uom_id._compute_price(price, price_uom))
                if not price_tracking:
                    price_tracking = u"%s" % price

                if price is not False:
                    if rule.compute_price == 'fixed':
                        price_tracking = u"%s%s" % (price_tracking, rule.currency_id.symbol)
                        price = convert_to_price_uom(rule.fixed_price)
                    elif rule.compute_price == 'percentage':
                        price_tracking = u"%s%s - %s%%" % (price_tracking, rule.currency_id.symbol, rule.percent_price)
                        price = (price - (price * (rule.percent_price / 100))) or 0.0
                    else:
                        # complete formula
                        price_limit = price
                        discount = (price * (rule.price_discount / 100))
                        price_tracking = u"%s %s %s%%" % (price_tracking, rule.percent_sign, rule.price_discount)
                        if rule.percent_sign == '+':
                            price = (price + discount) or 0.0
                        else:
                            price = (price - discount) or 0.0
                        if rule.price_round:
                            price = tools.float_round(price, precision_rounding=rule.price_round)
                            price_tracking = u"round(%s, rule.price_round)" % price_tracking

                        if rule.price_surcharge:
                            price_surcharge = convert_to_price_uom(rule.price_surcharge)
                            price += price_surcharge
                            price_tracking = u"%s + %s%s" % (price_tracking, price_surcharge, rule.currency_id.symbol)

                        if rule.price_min_margin:
                            price_min_margin = convert_to_price_uom(rule.price_min_margin)
                            price = max(price, price_limit + price_min_margin)
                            price_tracking = u"max(%s, %s)" % (price_tracking, price_limit + price_min_margin)

                        if rule.price_max_margin:
                            price_max_margin = convert_to_price_uom(rule.price_max_margin)
                            price = min(price, price_limit + price_max_margin)
                            price_tracking = u"min(%s, %s)" % (price_tracking, price_limit + price_max_margin)
                    suitable_rule = rule
                break
            # Final price conversion into pricelist currency
            if suitable_rule and suitable_rule.compute_price != 'fixed' and suitable_rule.base != 'pricelist':
                if suitable_rule.base == 'standard_price':
                    # The cost of the product is always in the company currency
                    price = product.cost_currency_id.compute(price, self.currency_id, round=False)
                else:
                    price = product.currency_id.compute(price, self.currency_id, round=False)
            if self._context.get("track", False):
                price_track.append(str(base_price)+"@"+str(suitable_rule.id if suitable_rule else "no_"+str(self.id))+"@"+str(price))

            results[product.id] = (price, suitable_rule and suitable_rule.id or False, price_tracking, price_track)
        for k,v in results.items():
            if type(v) == type(0.0):
                results[k] = (1.0, False, '', [])
        return results

    #
    # def price_get(self, cr, uid, ids, prod_id, qty, partner=None, context=None, product=None):
    #     return dict((key, price[0]) for key, price in
    #                 self.price_rule_get(cr, uid, ids, prod_id, qty, partner=partner, context=context,
    #                                     product=product).items())
    #
    # def price_rule_get(self, cr, uid, ids, prod_id, qty, partner=None, context=None, product=None):
    #     if not product:
    #         product = self.pool.get('product.product').browse(cr, uid, prod_id, context=context)
    #     res_multi = self.price_rule_get_multi(cr, uid, ids, products_by_qty_by_partner=[(product, qty, partner)],
    #                                           context=context)
    #     res = res_multi[prod_id]
    #     return res


class PricelistItem(models.Model):
    _inherit = 'product.pricelist.item'
    _order = " apply_supplier_id, applied_on, attribute_set_id, price_calculation_group, product_brand_id, product_name, min_uvp desc, min_quantity desc, categ_id desc"

    supplier_ids = fields.One2many(comodel_name='res.partner', string='Suppliers',
                                   help='Purchase Price calculation is only valid for this Supplier.', store=False,
                                   domain=[('supplier', '=', True)], copy=True, related='pricelist_id.supplier_ids',
                                   readonly=True)
    apply_supplier_id = fields.Many2one(comodel_name='res.partner', string='Supplier',
                                        help='Sale Price calculation is only valid for this Supplier.',
                                        domain=[('supplier', '=', True)], copy=True, track_visibility='onchange')
    min_uvp = fields.Float(name='Min. UVP', copy=True, default=0.00, track_visibility='onchange')
    product_net_weight = fields.Float(name='Net weight greater than',
                                      help="If product net weight is greater or equal to this value then rules will be applied.", track_visibility='onchange')
    product_gross_weight = fields.Float(string='Brutto', name='Net weight greater than',
                                        help="If product weight is greater or equal to this value then rules will be applied.",
                                        track_visibility='onchange')
    product_name = fields.Char(string='Product Name contain', help='Product name contains this text', track_visibility='onchange')
    product_brand_id = fields.Many2one('grimm.product.brand', string='Brand', track_visibility='onchange')
    percent_sign = fields.Selection([('-', '-'), ('+', '+')], string='Percent Sign', default='-',
                                    required=True, track_visibility='onchange')
    base = fields.Selection(selection_add=[('rrp_price', 'List Price')], track_visibility='onchange')
    price_calculation_group = fields.Many2one("product.price.group", string="Price Calculation Group", copy=True, track_visibility='onchange')
    attribute_set_id = fields.Many2one('product.attribute.set', string='Attribute set', copy=False, track_visibility='onchange')
    min_quantity = fields.Integer(
        'Min. Quantity', default=0,
        help="For the rule to apply, bought/sold quantity must be greater "
             "than or equal to the minimum quantity specified in this field.\n"
             "Expressed in the default unit of measure of the product.", track_visibility='onchange')
    applied_on = fields.Selection([
        ('3_global', 'Global'),
        ('2_product_category', ' Product Category'),
        ('1_product', 'Product'),
        ('0_product_variant', 'Product Variant')], "Apply On",
        default='3_global', required=True,
        help='Pricelist Item applicable on selected option', track_visibility='onchange')
    date_start = fields.Date('Start Date', help="Starting date for the pricelist item validation",
                             track_visibility='onchange')
    date_end = fields.Date('End Date', help="Ending valid for the pricelist item validation",
                           track_visibility='onchange')
    price_round = fields.Float(
        'Price Rounding', digits='Product Price',
        help="Sets the price so that it is a multiple of this value.\n"
             "Rounding is applied after the discount and before the surcharge.\n"
             "To have prices that end in 9.99, set rounding 10, surcharge -0.01",
        track_visibility='onchange')
    price_min_margin = fields.Float(
        'Min. Price Margin', digits='Product Price',
        help='Specify the minimum amount of margin over the base price.',
        track_visibility='onchange')
    price_max_margin = fields.Float(
        'Max. Price Margin', digits='Product Price',
        help='Specify the maximum amount of margin over the base price.',
        track_visibility='onchange')
    name_alt = fields.Char('Alternate Name', help="Explicit rule name for this pricelist line.")

    def copy_name(self):
        self.name_alt = self.name

    @api.depends('categ_id', 'product_tmpl_id', 'product_id', 'compute_price', 'fixed_price',
                 'pricelist_id', 'percent_price', 'price_discount', 'price_surcharge', 'percent_sign',
                 'base_pricelist_id')
    def _get_pricelist_item_name_price(self):
        for item in self:
            if item.categ_id and item.applied_on == '2_product_category':
                item.name = _("Category: %s") % (item.categ_id.display_name)
            elif item.product_tmpl_id and item.applied_on == '1_product':
                item.name = _("Product: %s") % (item.product_tmpl_id.display_name)
            elif item.product_id and item.applied_on == '0_product_variant':
                item.name = _("Variant: %s") % (
                    item.product_id.with_context(display_default_code=False).display_name)
            else:
                item.name = _("All Products")

            if item.compute_price == 'fixed':
                decimal_places = self.env['decimal.precision'].precision_get('Product Price')
                if item.currency_id.position == 'after':
                    item.price = "%s %s" % (
                        float_repr(
                            item.fixed_price,
                            decimal_places,
                        ),
                        item.currency_id.symbol,
                    )
                else:
                    item.price = "%s %s" % (
                        item.currency_id.symbol,
                        float_repr(
                            item.fixed_price,
                            decimal_places,
                        ),
                    )
            elif item.compute_price == 'percentage':
                item.price = _("%s %% discount") % (item.percent_price)
            else:
                base_dict = {'rrp_price': _('List Price'), 'standard_price': _('Purchase Price'),
                             'pricelist': _('Other Pricelist'), 'list_price': _('Public Price')}
                if item.base == 'pricelist':
                    base_price = '%s' % item.base_pricelist_id.name
                else:
                    base_price = base_dict.get(item.base, 'Unknown')

                item.price = _("%s %s %s%% + %s%s") % (
                    base_price,
                    item.percent_sign, item.price_discount, item.price_surcharge, item.currency_id.symbol,
                )

    def get_products(self):
        """
        get all products, which is related with these rules
        :return: list of products
        """

        def get_categ_child_ids(categ):
            """
            get child category ids of category categ
            :param categ: parent category
            :return: list of all child category ids (child of child too)
            """
            res = []
            res.extend((categ.child_id.ids))
            for child in categ.child_id:
                res.extend(get_categ_child_ids(child))
            return res

        product_ids = []
        for rule in self:
            domain_filter = []
            # applied_on
            if rule.applied_on == '3_global':
                pass
            elif rule.applied_on == '2_product_category' and rule.categ_id:
                categ_ids = [rule.categ_id.id]
                categ_ids.extend(get_categ_child_ids(rule.categ_id))
                if categ_ids:
                    domain_filter.append(('categ_id', 'in', categ_ids))
            elif rule.applied_on == '1_product' and rule.product_tmpl_id:
                domain_filter.append(('product_tmpl_id', '=', rule.product_tmpl_id.id))
            elif rule.applied_on == '0_product_variant' and rule.product_id:
                domain_filter.append(('id', '=', rule.product_tmpl_id.id))

            supplier_ids = []
            if rule.supplier_ids:
                for supplier in rule.supplier_ids:
                    supplier_ids.append(supplier.id)
                    if supplier.child_ids:
                        for child in supplier.child_ids:
                            if child.property_supplier_pricelist and child.property_supplier_pricelist != rule:
                                continue
                            supplier_ids.append(child.id)

            # apply_supplier_id
            if rule.apply_supplier_id:
                supplier_ids.append(rule.apply_supplier_id.id)
                if rule.apply_supplier_id.child_ids:
                    for child in rule.apply_supplier_id.child_ids:
                        supplier_ids.append(child.id)
            if supplier_ids:
                suppliers = self.env['product.supplierinfo'].search([('name', 'in', supplier_ids)])
                _template_ids = [supplier.product_tmpl_id.id for supplier in suppliers if supplier.product_tmpl_id]
                _product_ids = [supplier.product_id.id for supplier in suppliers if supplier.product_id]
                if _template_ids and _product_ids:
                    domain_filter.append('|')
                if _template_ids:
                    domain_filter.append(('product_tmpl_id', 'in', _template_ids))
                if _product_ids:
                    domain_filter.append(('id', 'in', _product_ids))

            # price_calculation_group
            if rule.price_calculation_group:
                domain_filter.append(('price_calculation_group', '=', rule.price_calculation_group.id))

            # product name contains
            if rule.product_name:
                domain_filter.append(('display_name', '=ilike', rule.product_name))

            # brand
            if rule.product_brand_id:
                domain_filter.append(('product_brand_id', '=', rule.product_brand_id.id))

            # attribute set
            if rule.attribute_set_id:
                domain_filter.append(('attribute_set_id', '=', rule.attribute_set_id.id))

            # Min UVP
            if rule.min_uvp:
                domain_filter.append(('rrp_price', '>=', rule.min_uvp))
            # _logger.info(domain_filter)
            products = self.env['product.product'].search_read(domain_filter, fields=['id'])
            _product_ids = [product['id'] for product in products]
            # _logger.info(products)
            # _logger.info(product_ids)
            product_ids.extend(_product_ids)

        expired_products = self.env['product.product'].get_product_expired_special_purchase_price()
        product_ids.extend(expired_products.ids)
        product_ids = set(product_ids)
        # _logger.info(product_ids)
        return self.env['product.product'].browse(product_ids)

    def check_products_prices(self, pricelist=None):
        products_to_update = self.get_products()
        product_ids = products_to_update.ids if products_to_update else []
        length = len(product_ids)
        _logger.info('%s Products to update on Magento', length)
        counter = 0
        for product_id in products_to_update:
            counter += 1
            try:
                is_available = self.env['product.update.queue'].search([('product_id', '=', product_id.id)], limit=1, )
                if not is_available:
                    self.env['product.update.queue'].create({'product_id': product_id.id})
                    _logger.info("[%s/%s] added Product %s into the queue" % (counter, length, product_id.id))
            except Exception as e:
                _logger.warn(str(e))
                _logger.info("[%s/%s] can't add Product %s into the queue" % (counter, length, product_id.id))

    def check_shopware_products_prices(self, pricelist=None):
        products_to_update = self.get_products()
        product_ids = products_to_update.ids if products_to_update else []
        length = len(product_ids)
        _logger.info('%s Products to update on Shopware', length)
        counter = 0
        for product_id in products_to_update:
            counter += 1
            is_shopware = self.env['shopware.product.template'].search([('openerp_id', '=', product_id.product_tmpl_id.id)], limit=1, )
            if is_shopware:
                try:
                    is_available = self.env['shopware.product.update.queue'].search([('product_id', '=', product_id.id)],limit=1, )
                    if is_available:
                        is_available.is_done = False
                    else:
                        self.env['shopware.product.update.queue'].create({'product_id': product_id.id, 'is_done':False})
                        _logger.info(
                            "[%s/%s] added Shopware Product %s into the queue for price update" % (counter, length, product_id.id))
                except Exception as e:
                    _logger.warn(str(e))
                    _logger.info("[%s/%s] can't add Product %s into the shopware product price queue" % (
                    counter, length, product_id.id))

    def recalculate_old(self, pricelist=None):
        LIMIT = 1000
        products_to_update = self.get_products()
        _logger.info('RECALCULATE: found %s products to update' % (len(products_to_update)))
        res = {}
        page = 0
        products = products_to_update[page * LIMIT:(page + 1) * LIMIT]
        while products:
            _logger.info('RECALCULATE: Page %s Length %s' % (page, len(products)))
            _res = products.update_price_history(pricelist=pricelist)
            res.update(_res)
            page += 1
            products = products_to_update[page * LIMIT:(page + 1) * LIMIT]
        if res:
            """
            for product_id, values in res.iteritems():
                product = self.env['product.product'].browse(product_id)
                product.write(values)
            """
            products = self.env['product.product'].browse(list(res.keys()))
            product_tmpl_ids = [product.product_tmpl_id.id for product in products]
            product_tmpl_ids = set(product_tmpl_ids)
            self.env['product.template'].browse(product_tmpl_ids).with_context({'no_trigger_price_again': True}).write(
                {'update_prices_trigger': True})

    def write(self, vals):
        res = super(PricelistItem, self).write(vals)
        # self.recalculate()
        return res

    def create(self, vals):
        res = super(PricelistItem, self).create(vals)
        # res.recalculate()
        return res
