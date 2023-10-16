# -*- coding: utf-8 -*-
# Copyright 2017 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import logging

from re import search as re_search
from datetime import datetime, timedelta
import dateutil.parser
from odoo import _
import hashlib
import copy
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo.addons.queue_job.exception import NothingToDoJob, FailedJobError
from odoo.addons.connector.exception import IDMissingInBackend
from ...components.mapper import normalize_datetime
from ...exception import OrderImportRuleRetry

_logger = logging.getLogger(__name__)


class SaleOrderBatchImporter(Component):
    _name = 'shopware6.sale.order.batch.importer'
    _inherit = 'shopware6.delayed.batch.importer'
    _apply_on = 'shopware6.sale.order'

    def _import_record(self, shopware6_id, job_options={}, **kwargs):
        job_options.update({
            'max_retries': 0,
            'priority': 5,
        })
        return super(SaleOrderBatchImporter, self)._import_record(
            shopware6_id, job_options=job_options)

    def run(self, filters=None):
        """ Run the synchronization """
        if filters is None:
            filters = []
        shopware6_ids = self.backend_adapter.search(filters)
        for shopware6_id in shopware6_ids:
            shopware_sale_id = shopware6_id.get('id')
            self._import_record(shopware_sale_id, job_options={'description':"Import %s sale order from shopware."%shopware6_id.get('attributes',{}).get("orderNumber","")})


class Shopware6SaleImportRule(Component):
    _name = 'shopware6.sale.import.rule'
    _inherit = 'base.shopware6.connector'
    _apply_on = 'shopware6.sale.order'
    _usage = 'shopware6.sale.import.rule'

    def _rule_always(self, record, payment_method_mapping, payment_status):
        """ Always import the order """
        return True

    def _rule_never(self, record, payment_method_mapping, payment_status):
        """ Never import the order """
        raise NothingToDoJob('Orders with payment method %s '
                             'are never imported.' %
                             record['payment']['method'])

    def _rule_authorized(self, record, payment_method_mapping, payment_status):
        """ Import the order only if payment has been authorized. """
        if payment_status != 'authorized':
            raise OrderImportRuleRetry('The order payment has not been authorized.\n'
                                       'The import will be retried later.', seconds=30*60)

    def _rule_paid(self, record, payment_method_mapping, payment_status):
        """ Import the order only if it has received a payment """
        if payment_status != 'paid':
            raise OrderImportRuleRetry('The order has not been paid.\n'
                                       'The import will be retried later.', seconds=30*60)

    _rules = {'always': _rule_always,
              'paid': _rule_paid,
              'authorized': _rule_authorized,
              'never': _rule_never,
              }

    def _rule_global(self, record, method):
        """ Rule always executed, whichever is the selected rule """
        # the order has been canceled since the job has been created

        order_date = record.get("data", {}).get("attributes", {}).get("createdAt","")
        max_days = method.days_before_cancel
        if max_days:
            fmt = '%Y-%m-%d %H:%M:%S'
            order_date = datetime.strptime(dateutil.parser.parse(order_date).strftime('%Y-%m-%d %H:%M:%S'),"%Y-%m-%d %H:%M:%S")


            if order_date + timedelta(days=max_days) < datetime.now():
                raise NothingToDoJob('Import of the order %s canceled '
                                     'because it has not been paid since %d '
                                     'days' % (record.get("data", {}).get("attributes", {}).get("orderNumber",""), max_days))

    def get_latest_transaction(self, transactions=[]):
        '''
        This method return the latest transaction based on updateAt field.
        :param transactions:
        :return:
        '''
        extra_dict = {}
        for l in transactions:
            attr = l.get("attributes", {})
            sort_field = attr.get('createdAt')
            if attr.get("updatedAt", False) != None:
                sort_field = attr.get('updatedAt')
            extra_dict[datetime.strptime(sort_field.split("+")[0], "%Y-%m-%dT%H:%M:%S.%f")] = attr
        return extra_dict[sorted(extra_dict)[-1]]

    def check(self, record):
        """ Check whether the current sale order should be imported
        or not. It will actually use the payment method configuration
        and see if the choosed rule is fullfilled.

        :returns: True if the sale order should be imported
        :rtype: boolean
        """
        sale_adapter = self.component(usage='backend.adapter', model_name='shopware6.sale.order')
        order_id = record.get("data",{}).get("id", False)
        payment_mode_id = False
        payment_method_mapping = False

        shopware_payment_data = self.get_latest_transaction(sale_adapter.get_transactions(order_id).get("data", [[]]))

        #shopware_payment_data = sale_adapter.get_transactions(order_id).get("data", [[]])[-1].get("attributes", {})
        payment_id = shopware_payment_data.get("paymentMethodId", False)
        if payment_id:
            odoo_payment = self.backend_record.payment_mode_mapping_ids.filtered(lambda payment: payment.shopware6_id == payment_id)
            if odoo_payment and odoo_payment.odoo_payment_mode_id:
                payment_mode_id = odoo_payment.odoo_payment_mode_id
                payment_method_mapping = odoo_payment


        if not payment_mode_id:
            payment_method_adapter = self.component(usage='backend.adapter',model_name='shopware6.account.payment.mode')
            payment_data = payment_method_adapter.read(payment_id).get("data", {}).get("attributes", {}).get("name","")
            raise FailedJobError(
                "\n\nThe configuration is missing for the Payment Mode '%s'.\n\n"
                "Resolution:\n"
                "- Go to "
                "'Shopware6 Backend > Click on 'Synchronize Metadata' button\n"
                "- Now add payment mode mapping in Shopware6 Backend '%s'\n"
                "Process or create a new one." % (payment_data,
                                                  payment_data))
        self._rule_global(record, payment_method_mapping)

        status_id = shopware_payment_data.get("stateId", False)
        payment_status = sale_adapter.get_machine_state(status_id).get("data", {}).get("attributes", {}).get("technicalName","")

        self._rules[payment_method_mapping.import_rule](self, record, payment_method_mapping, payment_status)


class SaleOrderImportMapper(Component):

    _name = 'shopware6.sale.order.mapper'
    _inherit = 'shopware6.import.mapper'
    _apply_on = 'shopware6.sale.order'
    partner_id = None
    partner_invoice_id = None
    partner_shipping_id = None



    #children = [('details', 'shopware6_order_line_ids', 'shopware6.sale.order.line'),]

    def _add_shipping_line(self, map_record, values):
        record = map_record.source
        amount_incl = float(record.get('base_shipping_incl_tax') or 0.0)
        amount_excl = float(record.get('shipping_amount') or 0.0)
        line_builder = self.component(usage='order.line.builder.shipping')
        # add even if the price is 0, otherwise odoo will add a shipping
        # line in the order when we ship the picking
        if self.options.tax_include:
            discount = float(record.get('shipping_discount_amount') or 0.0)
            line_builder.price_unit = (amount_incl - discount)
        else:
            line_builder.price_unit = amount_excl

        if values.get('carrier_id'):
            carrier = self.env['delivery.carrier'].browse(values['carrier_id'])
            line_builder.product = carrier.product_id

        line = (0, 0, line_builder.get_line())
        values['order_line'].append(line)
        return values

    def _add_cash_on_delivery_line(self, map_record, values):
        record = map_record.source
        amount_excl = float(record.get('cod_fee') or 0.0)
        amount_incl = float(record.get('cod_tax_amount') or 0.0)
        if not (amount_excl or amount_incl):
            return values
        line_builder = self.component(usage='order.line.builder.cod')
        tax_include = self.options.tax_include
        line_builder.price_unit = amount_incl if tax_include else amount_excl
        line = (0, 0, line_builder.get_line())
        values['order_line'].append(line)
        return values

    def _add_gift_certificate_line(self, map_record, values):
        record = map_record.source
        # if gift_cert_amount is zero or doesn't exist
        if not record.get('gift_cert_amount'):
            return values
        amount = float(record['gift_cert_amount'])
        if amount == 0.0:
            return values
        line_builder = self.component(usage='order.line.builder.gift')
        line_builder.price_unit = amount
        if 'gift_cert_code' in record:
            line_builder.gift_code = record['gift_cert_code']
        line = (0, 0, line_builder.get_line())
        values['order_line'].append(line)
        return values

    def _add_gift_cards_line(self, map_record, values):
        record = map_record.source
        # if gift_cards_amount is zero or doesn't exist
        if not record.get('gift_cards_amount'):
            return values
        amount = float(record['gift_cards_amount'])
        if amount == 0.0:
            return values
        line_builder = self.component(usage='order.line.builder.gift')
        line_builder.price_unit = amount
        if 'gift_cards' in record:
            gift_code = ''
            gift_cards_serialized = record.get('gift_cards')
            codes = re_search(r's:1:"c";s:\d+:"(.*?)"', gift_cards_serialized)
            if codes:
                gift_code = ', '.join(codes.groups())
            line_builder.gift_code = gift_code
        line = (0, 0, line_builder.get_line())
        values['order_line'].append(line)
        return values

    def _add_store_credit_line(self, map_record, values):
        record = map_record.source
        if not record.get('customer_balance_amount'):
            return values
        amount = float(record['customer_balance_amount'])
        if amount == 0.0:
            return values
        line_builder = self.component(usage='order.line.builder.magento.store_credit')
        line_builder.price_unit = amount
        line = (0, 0, line_builder.get_line())
        values['order_line'].append(line)
        return values

    def _add_rewards_line(self, map_record, values):
        record = map_record.source
        if not record.get('reward_currency_amount'):
            return values
        amount = float(record['reward_currency_amount'])
        if amount == 0.0:
            return values
        line_builder = self.component(usage='order.line.builder.magento.rewards')
        line_builder.price_unit = amount
        line = (0, 0, line_builder.get_line())
        values['order_line'].append(line)
        return values

    # def finalize(self, map_record, values):
    #     values.setdefault('order_line', [])
    #     # values = self._add_shipping_line(map_record, values)
    # #     #values = self._add_cash_on_delivery_line(map_record, values)
    # #     #values = self._add_gift_certificate_line(map_record, values)
    # #     #values = self._add_gift_cards_line(map_record, values)
    # #     #values = self._add_store_credit_line(map_record, values)
    # #     #values = self._add_rewards_line(map_record, values)
    # #     #values.update({
    # #     #    'partner_id': self.partner_id,
    # #     #    'partner_invoice_id': self.partner_invoice_id,
    # #     #    'partner_shipping_id': self.partner_shipping_id,
    # #     #})
    #     onchange = self.component(
    #         usage='ecommerce.onchange.manager.sale.order'
    #     )
    #     return onchange.play(values, values['shopware6_order_line_ids'])

    # @mapping
    # def set_transaction_id(self, record):
    #     if record.get('descriptor'):
    #         return {'shop_payment_ref' : record.get('descriptor','')}

    @mapping
    def set_payment_method(self, record):
        order_id = record.get("data", [{}, {}]).get("id", False)
        res = {}
        res["prepayment"] = False
        if order_id:
            sale_adapter = self.component(usage='backend.adapter')
            #payment_id = sale_adapter.get_transactions(order_id).get("data", [[]])[-1].get("attributes", {}).get("paymentMethodId", False)
            order_import_rule = self.component(usage='shopware6.sale.import.rule')
            payment_id = order_import_rule.get_latest_transaction(sale_adapter.get_transactions(order_id).get("data", [[]])).get("paymentMethodId", False)
            if payment_id:
                odoo_payment = self.backend_record.payment_mode_mapping_ids.filtered(lambda payment: payment.shopware6_id == payment_id)
                if odoo_payment and odoo_payment.odoo_payment_mode_id:
                    res["payment_mode_id"] = odoo_payment.odoo_payment_mode_id.id
                    if odoo_payment.odoo_payment_mode_id.id == 3:
                        res["prepayment"] = True
        return res





    @mapping
    def set_shopware6_total(self, record):
        shopware6_total = record.get("data", [{}, {}]).get("attributes", {}).get("amountTotal", False)
        if shopware6_total:
            return {'shopware6_amount_total': shopware6_total}
        return {}

    @mapping
    def set_order_meta_data(self, record):
        res = {}
        date_order = record.get("data", [{}, {}]).get("attributes", {}).get("orderDateTime", False)
        if date_order:
            res["date_order"] = datetime.strptime(dateutil.parser.parse(date_order).strftime('%Y-%m-%d %H:%M:%S'),"%Y-%m-%d %H:%M:%S")-timedelta(hours=2)
        return res

    @mapping
    def name(self, record):
        attr = record.get("data").get("attributes")
        prefix = self.backend_record.sale_prefix
        res = {}
        name = str(prefix + attr.get('orderNumber')) if prefix else attr.get('orderNumber')
        res["name"] = name
        if self.backend_record.fiscal_position_id:
            res["fiscal_position_id"] = self.backend_record.fiscal_position_id.id
        return res

    @mapping
    def set_partner_id(self, record):
        '''
        Here we are assign customer if we have already in odoo based on shopware6 id.
        If id is not there we use temp partner_id and rest condition we will check in after_import method,
        and will be assign actual patner_id, partner_shipping_id, partner_invoice_id.
        :param record:
        :return:
        '''

        partner_id = record.get("odoo_partner_id", False)
        partner_invoice_id = record.get("odoo_partner_invoice_id", False)
        partner_shipping_id = record.get("odoo_partner_shipping_id", False)
        if partner_invoice_id and not partner_shipping_id:
            partner_shipping_id = partner_invoice_id
        if partner_shipping_id and not partner_invoice_id:
            partner_invoice_id = partner_shipping_id
        if not partner_shipping_id and not partner_invoice_id:
            partner_invoice_id = partner_shipping_id = partner_id
        return {'partner_id':partner_id,'partner_invoice_id':partner_invoice_id,'partner_shipping_id':partner_shipping_id}

    @mapping
    def set_warehouse(self, record):
        if self.backend_record.warehouse_id:
            return {'warehouse_id': self.backend_record.warehouse_id.id}
        else:
            return {}

    @mapping
    def map_company_id(self, record):
        if self.work.collection.default_company_id:
            return {'company_id':self.work.collection.default_company_id.id}

    @mapping
    def backend_id(self, record):
        return {'backend_id': self.backend_record.id}

    @mapping
    def user_id(self, record):
        """ Do not assign to a Salesperson otherwise sales orders are hidden
        for the salespersons (access rules)"""
        return {'user_id': False}

    @mapping
    def set_transaction_id(self, record):
        res = {}
        try:
            # For rate pay we receive Transaction ID in descriptor
            for trans in record.get("included", []):
                if trans.get("attributes", {}).get("descriptor", False):
                    res["shop_payment_ref"] = trans.get("attributes", {}).get("descriptor")
        except:
            return res

        if not res:
            try:
                # For PayPal we receive Transaction ID in transaction call
                order_id = record.get("data", [{}, {}]).get("id", False)
                sale_adapter = self.component(usage='backend.adapter')
                order_import_rule = self.component(usage='shopware6.sale.import.rule')
                transaction = order_import_rule.get_latest_transaction(sale_adapter.get_transactions(order_id).get("data", [[]]))
                if transaction and transaction.get("customFields",{}).get("swag_paypal_resource_id",False):
                    res["shop_payment_ref"] = transaction.get("customFields",{}).get("swag_paypal_resource_id",False)
            except:
                return res
        return res


class SaleOrderImporter(Component):
    _name = 'shopware6.sale.order.importer'
    _inherit = 'shopware6.importer'
    _apply_on = 'shopware6.sale.order'


    def _must_skip(self):
        """ Hook called right after we read the data from the backend.

        If the method returns a message giving a reason for the
        skipping, the import will be interrupted and the message
        recorded in the job (if the import is called directly by the
        job, not by dependencies).

        If it returns None, the import will continue normally.

        :returns: None | str | unicode
        """
        if self.binder.to_internal(self.shopware6_id):
            return _('This Shopware order is already imported')

    def _before_import(self):
        rules = self.component(usage='shopware6.sale.import.rule')
        rules.check(self.shopware_record)

    # def _before_import(self):
    #     rules = self.component(usage='shopware6.sale.import.rule')
    #     rules.check(self.shopware_record)

    def _after_import(self, binding):
        '''
        Shopware store order line in different model so we have to fetch order line data after fetched order.
        :param binding:
        :return:
        '''
        line_binder = self.binder_for('shopware6.sale.order.line')
        line_mapper = self.component(usage='import.mapper', model_name='shopware6.sale.order.line')
        order_lines = self.backend_adapter.get_order_lines(self.shopware6_id).get("data",[])
        for line in order_lines:
            if ((line.get("attributes",{}).get("productId", False) or line.get("attributes",{}).get("parentId", False)) and line.get("attributes").get("payload", {}).get("productNumber", "XXXXXXX") != "*"):
                line["shopware6_customer_group"] =binding.openerp_id.shopware6_customer_group_old
                map_line = line_mapper.map_record(line)
                line_vals = map_line.values(for_create=True)
                line_vals.update({'order_id':binding.openerp_id.id,'shopware6_order_id':binding.id,'shopware6_id':line.get("id","")})
                line_id = self.env['shopware6.sale.order.line'].create(line_vals)

        # creating voucher code line after normal order line
        for line in order_lines:
            if type(line.get("attributes").get("payload")) == type({}) and line.get("attributes").get("payload", {}).get("code", False):
                line["shopware6_customer_group"] =binding.openerp_id.shopware6_customer_group_old
                map_line = line_mapper.map_record(line)
                line_vals = map_line.values(for_create=True)
                line_vals.update({'order_id':binding.openerp_id.id,'shopware6_order_id':binding.id,'shopware6_id':line.get("id","")})
                line_id = self.env['shopware6.sale.order.line'].create(line_vals)

    def assign_address(self, partner_id, val_dict, type = False, model="shopware6.address"):
        temp_record = copy.deepcopy(val_dict)
        addr_mapper = self.component(usage='import.mapper', model_name=model)
        map_record = addr_mapper.map_record(temp_record)
        res = map_record.values()
        del res["backend_id"]
        if type:
            res["type"] = type
            partner_id.write(res)
        else:
            partner_id.write({'street':res.get("street",""),'city':res.get("city",""),'zip':res.get("zip","")})

    def create_partner(self, rec_id, model="shopware6.res.partner"):
        partner_binder = self.binder_for(model)
        partner_binding = partner_binder.to_internal(rec_id)
        if partner_binding:
            partner = partner_binding.openerp_id
        else:
            importer = self.component(usage='record.importer', model_name=model)
            importer.run(rec_id)
            partner_binding = partner_binder.to_internal(rec_id)
            partner = partner_binding.openerp_id
        return partner


    def _import_addresses(self):
        record = self.shopware_record
        order_customer = record.get("included",[{},{}])[1].get("attributes",{}).get("customerId",False)
        billing_address = record.get("data", {}).get("attributes", {}).get("billingAddressId", False)

        customer_data = self.backend_adapter.get_customer(order_customer)
        is_guest_customer = customer_data.get("data", {}).get("attributes", {}).get("guest", False)
        customer_email = customer_data.get("data", {}).get("attributes", {}).get("email", False)

        main_partner = False
        if is_guest_customer:
            main_partner = self.env['res.partner'].search([('email', '=', customer_email)], limit=1) # If guest customer search with email and assign to order partner.
        if not main_partner:
            main_partner = self.create_partner(order_customer, model="shopware6.res.partner") # If no partner existing create and assign binding.

        record["odoo_partner_id"] = main_partner.id

        #Now we wanted to avoid duplication of address, because for each order shopware assign new order address
        # So we have decided to create md5 hash and compare with existing address for main partner.
        odoo_addresses = {} # Create json with hash and record id.
        for child in main_partner.child_ids:
            odoo_hash_string = "{} {} {} {}".format(child.name, child.street, child.zip, child.city).lower()
            odoo_addresses[hashlib.md5(odoo_hash_string.encode('utf-8')).hexdigest()] = child

        order_addresses = self.backend_adapter.order_address(record.get('data').get('id')) # Now get all addresses of sale order from Shopware
        address_binder = self.binder_for('shopware6.address')
        for address in order_addresses.get("data", []):
            address_data = address.get("attributes", {})
            shopware_hash_string = "{} {} {} {} {}".format(address_data.get("firstName", ""),address_data.get("lastName", ""), address_data.get("street", ""), address_data.get("zipcode", ""), address_data.get("city", "")).lower()
            shopware_hash_string = hashlib.md5(shopware_hash_string.encode('utf-8')).hexdigest()
            if odoo_addresses.get(shopware_hash_string, False): # If same address available using hash comparision, get the address
                odoo_shopware_address = []
                for addr in odoo_addresses.get(shopware_hash_string).shopware6_address_ids:
                    odoo_shopware_address.append(addr.shopware6_id)
                if address.get("id","") not in odoo_shopware_address:# Adding new binding of address if not available in odoo
                    self.env.cr.execute("INSERT INTO shopware6_address (backend_id, shopware6_id, openerp_id) VALUES (%s,'%s', %s)" % (self.backend_record.id,address.get("id",""), odoo_addresses.get(shopware_hash_string).id))
                if address.get("id") == billing_address:
                    record["odoo_partner_invoice_id"] = odoo_addresses.get(shopware_hash_string).id
                else:
                    record["odoo_partner_shipping_id"] = odoo_addresses.get(shopware_hash_string).id
            else:
                address_importer = self.component(usage='record.importer', model_name='shopware6.address')
                address_importer.run(address.get("id"))
                partner_binding = address_binder.to_internal(address.get("id"))
                if address.get("id") == billing_address:
                    self.assign_address(partner_binding.openerp_id, address, type='invoice')
                    self.assign_address(main_partner, address)
                    main_partner.country_id = partner_binding.country_id.id
                    if address.get("attributes",{}).get("phoneNumber", False):
                        main_partner.phone = address.get("attributes",{}).get("phoneNumber", "")
                    record["odoo_partner_invoice_id"] = partner_binding.openerp_id.id
                else:
                    self.assign_address(partner_binding.openerp_id, address, type='delivery')
                    record["odoo_partner_shipping_id"] = partner_binding.openerp_id.id
                    if not main_partner.phone and address.get("attributes",{}).get("phoneNumber", False):
                        main_partner.phone = address.get("attributes",{}).get("phoneNumber", "")
                partner_binding.openerp_id.parent_id = main_partner.id

        return True

    def _import_dependencies(self):
        record = self.shopware_record
        self._import_addresses()

class SaleOrderLineImportMapper(Component):

    _name = 'shopware6.sale.order.line.mapper'
    _inherit = 'shopware6.import.mapper'
    _apply_on = 'shopware6.sale.order.line'

    @mapping
    def product_id(self, record):
        data = record.get("attributes")
        product_shopware_id = data.get('productId',False)
        product_sku = data.get("payload", {}).get("productNumber", "XXXXXXX")
        product_id = False
        return_dict = {}
        if product_shopware_id:
            binder = self.binder_for('shopware6.product.product')
            product_id = binder.to_internal(data['productId'], unwrap=True)
        else:
            product_id = self.env['product.product'].search(['|',('barcode', '=', product_sku),('default_code', '=', product_sku)],limit=1,)

        if not product_id:
            product_id = self.env['product.product'].search(['|',('barcode', '=', product_sku),('default_code', '=', product_sku)],limit=1,)

        if not product_id and data.get("payload", {}).get("code", False):
            product_id = self.env['product.product'].search([('default_code', '=', data.get("payload", {}).get("code", 'SHOPWARE6_DISCOUNT'))], limit=1,) # search product based on voucher code
            if not product_id:
                product_id = self.env['product.product'].search([('default_code', '=', 'SHOPWARE6_DISCOUNT')], limit=1, )
            line_description = product_id.description_sale if product_id else "Gutschrift code - "
            return_dict["name"] = "%s %s" % (line_description, data.get("payload", {}).get("code", ""))

        if not product_id and data.get("referencedId", False):
            value_binder = self.binder_for('shopware6.grimm_custom_product.option_value')
            option_value = value_binder.to_internal(data.get("referencedId", False), unwrap=True)
            if option_value:
                product_id = option_value.product_id.product_variant_id
        if not product_id:
            option_value = self.env['grimm_custom_product.option_value'].search([('sku', '=', product_sku)],limit=1,)
            if option_value:
                product_id = option_value.product_id.product_variant_id

        assert product_id, (
                "product_id %s or %s should have been imported in "
               "SaleOrderImporter._import_dependencies %s order line id" % (product_shopware_id, product_sku, record.get("id")))

        price_info = data.get("price")

        tax_amount = 0.0
        for tax in price_info.get("calculatedTaxes", []):
            tax_amount += tax.get("tax", 0.0)

        return_dict["product_id"] = product_id.id
        if record.get("shopware6_customer_group","") == "business":
            return_dict["price_unit"] = data.get("unitPrice")
        else:
            return_dict["price_unit"] = data.get("unitPrice") - (tax_amount/price_info.get("quantity",0))
            return_dict["shopware6_price_unit"] =  data.get("unitPrice") - (tax_amount/price_info.get("quantity",0))
        return_dict["product_uom_qty"] = data.get("quantity")
        return_dict["qty_to_invoice"] = data.get("quantity")
        return_dict["route_id"] = 6 # Set default route as Drop Shipping as requested from Fabian.
        return return_dict

    '''
    @mapping
    def discount_amount(self, record):
        discount_value = float(record.get('discount_amount') or 0)
        if self.options.tax_include:
            row_total = float(record.get('row_total_incl_tax') or 0)
        else:
            row_total = float(record.get('row_total') or 0)
        discount = 0
        if discount_value > 0 and row_total > 0:
            discount = 100 * discount_value / row_total
        result = {'discount': discount}
        return result

    @mapping
    def product_id(self, record):
        binder = self.binder_for('magento.product.product')
        product = binder.to_internal(record['product_id'], unwrap=True)
        assert product, (
            "product_id %s should have been imported in "
            "SaleOrderImporter._import_dependencies" % record['product_id'])
        return {'product_id': product.id}

    @mapping
    def product_options(self, record):
        result = {}
        ifield = record['product_options']
        if ifield:
            import re
            options_label = []
            clean = re.sub(r'\w:\w:|\w:\w+;', '', ifield)
            for each in clean.split('{'):
                if each.startswith('"label"'):
                    split_info = each.split(';')
                    options_label.append('%s: %s [%s]' % (split_info[1],
                                                          split_info[3],
                                                          record['sku']))
            notes = "".join(options_label).replace('""', '\n').replace('"', '')
            result = {'notes': notes}
        return result

    @mapping
    def price(self, record):
        result = {}
        base_row_total = float(record['base_row_total'] or 0.)
        base_row_total_incl_tax = float(record['base_row_total_incl_tax'] or
                                        0.)
        qty_ordered = float(record['qty_ordered'])
        if self.options.tax_include:
            result['price_unit'] = base_row_total_incl_tax / qty_ordered
        else:
            result['price_unit'] = base_row_total / qty_ordered
        return result
    '''