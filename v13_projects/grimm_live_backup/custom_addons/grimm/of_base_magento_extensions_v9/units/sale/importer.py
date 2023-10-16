# -*- coding: utf-8 -*-

import copy

from odoo import _
from odoo.addons.component.core import Component
from odoo.addons.connector.components.mapper import mapping
from odoo.addons.connector_magento.components.mapper import  normalize_datetime

import logging

_logger = logging.getLogger(__name__)


class SaleOrderImporter(Component):
    _name = 'magento.sale.order.importer'
    _inherit = 'magento.sale.order.importer'
    _apply_on = 'magento.sale.order'

    def _set_amounts(self, record):
        amount_untaxed = float(record.get('base_subtotal')) + float(record.get('base_shipping_amount')) + float(
            record.get('base_discount_amount'))
        amount_tax = float(record.get('tax_amount'))
        amount_total = float(record.get('grand_total'))
        self.amounts = {'amount_untaxed': amount_untaxed, 'amount_tax': amount_tax, 'amount_total': amount_total}

    def _update_so_amounts(self, binding):
        order_id = self.binder.unwrap_binding(binding)

        query = """UPDATE sale_order
                   SET amount_untaxed={amount_untaxed}, amount_tax={amount_tax}, amount_total={amount_total}
                   WHERE id=%s""".format(**self.amounts) % (order_id.id)

        self.env.cr.execute(query)

    def _get_magento_data(self):
        res = super(SaleOrderImporter, self)._get_magento_data()
        order_lines_data = res.get('items', False)

        if order_lines_data:
            billing_address_data = res.get('billing_address', False)

            if billing_address_data and billing_address_data.get('country_id', False):
                country_code = billing_address_data['country_id']

                for line in order_lines_data:
                    line['billing_address'] = {'country_id': country_code}

        return res

    def _before_import(self):
        self._set_amounts(self.magento_record)
        return super(SaleOrderImporter, self)._before_import()

    def _after_import(self, binding):
        self._update_so_amounts(binding)
        if binding and binding.openerp_id:
            binding.openerp_id._onchange_salutation_text_offer_tmpl()
            binding.openerp_id._onchange_salutation_text_order_tmpl()
            binding.openerp_id._onchange_salutation_text_dn_tmpl()
        return super(SaleOrderImporter, self)._after_import(binding)

    def compare_billing_delivery_address(self, billing, delivery):
        if billing.get('firstname', None) != delivery.get('firstname', None):
            return False
        if billing.get('middlename', None) != delivery.get('middlename', None):
            return False
        if billing.get('lastname', None) != delivery.get('lastname', None):
            return False
        if billing.get('street', None) != delivery.get('street', None):
            return False
        if billing.get('country_id', None) != delivery.get('country_id', None):
            return False
        if billing.get('region', None) != delivery.get('region', None):
            return False
        if billing.get('postcode', None) != delivery.get('postcode', None):
            return False
        if billing.get('city', None) != delivery.get('city', None):
            return False
        if billing.get('telephone', None) != delivery.get('telephone', None):
            return False
        if billing.get('email', None) != delivery.get('email', None):
            return False
        return True

    def _import_addresses(self):

        record = self.magento_record

        # Magento allows to create a sale order not registered as a user
        is_guest_order = bool(int(record.get('customer_is_guest', 0) or 0))
        standard_import = False

        # For a guest order or when magento does not provide customer_id
        # on a non-guest order (it happens, Magento inconsistencies are
        # common)
        if (is_guest_order or not record.get('customer_id')):
            website_binder = self.binder_for('magento.website')
            oe_website_id = website_binder.to_internal(record['website_id'])

            # search an existing partner with the same email
            # partner = self.env['magento.res.partner'].search(
            #     [('emailid', '=', record['customer_email']),
            #      ('website_id', '=', oe_website_id)],
            #     limit=1)
            # guest order or no customer_id, always create new contact
            partner = False

            # if we have found one, we "fix" the record with the magento
            # customer id
            if partner:
                magento = partner.magento_id
                # If there are multiple orders with "customer_id is
                # null" and "customer_is_guest = 0" which share the same
                # customer_email, then we may get a magento_id that is a
                # marker 'guestorder:...' for a guest order (which is
                # set below).  This causes a problem with
                # "importer.run..." below where the id is cast to int.
                if str(magento).startswith('guestorder:'):
                    is_guest_order = True
                else:
                    record['customer_id'] = magento

            # no partner matching, it means that we have to consider it
            # as a guest order
            else:
                is_guest_order = True

        partner_binder = self.binder_for('magento.res.partner')
        if is_guest_order:
            # ensure that the flag is correct in the record
            record['customer_is_guest'] = True
            guest_customer_id = 'guestorder:%s' % record['increment_id']
            # "fix" the record with a on-purpose built ID so we can found it
            # from the mapper
            record['customer_id'] = guest_customer_id
            customer_group = record.get('customer_group_id')
            if customer_group:
                self._import_customer_group(customer_group)
            customer_record = copy.deepcopy(record['billing_address'])
            customer_record.update({
                'email': record.get('customer_email'),
                'taxvat': record.get('customer_taxvat'),
                'group_id': customer_group,
                'gender': record.get('customer_gender'),
                'store_id': record['store_id'],
                'created_at': normalize_datetime('created_at')(self,
                                                               record, ''),
                'updated_at': False,
                'created_in': False,
                'dob': record.get('customer_dob'),
                'website_id': record.get('website_id')
            })
            mapper = self.component(usage='import.mapper',
                                    model_name='magento.res.partner')
            map_record = mapper.map_record(customer_record)
            map_record.update(guest_customer=True)
            partner_binding = self.env['magento.res.partner'].create(
                map_record.values(for_create=True))
            partner_binder.bind(guest_customer_id,partner_binding)
        else:

            # we always update the customer when importing an order
            importer = self.component(usage='record.importer',
                                      model_name='magento.res.partner')
            importer.run(record['customer_id'])
            partner_binding = partner_binder.to_internal(record['customer_id'])

            standard_import = True

        partner = partner_binding.openerp_id

        # Import of addresses. We just can't rely on the
        # ``customer_address_id`` field given by Magento, because it is
        # sometimes empty and sometimes wrong.

        # The addresses of the sale order are imported as active=false
        # so they are linked with the sale order but they are not displayed
        # in the customer form and the searches.

        # We import the addresses of the sale order as Active = False
        # so they will be available in the documents generated as the
        # sale order or the picking, but they won't be available on
        # the partner form or the searches. Too many adresses would
        # be displayed.
        # They are never synchronized.

        # For the orders which are from guests, we let the addresses
        # as active because they don't have an address book.

        invoice_contact = None

        if standard_import:
            for contact in partner.child_ids:
                if contact.type == 'invoice':
                    invoice_contact = contact
                    break

            if invoice_contact and invoice_contact.company:
                partner_binding.write({
                    'name': contact.company,
                    'is_company': True,
                    'company': False,
                    'consider_as_company': True
                })
            else:
                partner_binding.write({'is_company': False, 'consider_as_company': False})

        addresses_defaults = {'parent_id': partner.id,
                              'magento_partner_id': partner_binding.id,
                              'email': record.get('customer_email', False),
                              'active': True,
                              'is_magento_order_address': True}

        addr_mapper = self.component(usage='import.mapper',
                                     model_name='magento.address')

        def create_address(address_record):
            map_record = addr_mapper.map_record(address_record)
            map_record.update(addresses_defaults)
            address_bind = self.env['magento.address'].with_context(skip_address_sync_from_parent=True).create(
                map_record.values(for_create=True,
                                  parent_partner=partner))
            return address_bind.openerp_id.id

        billing_id = create_address(record['billing_address'])
        is_billing_delivery_same = self.compare_billing_delivery_address(record['billing_address'],
                                                                         record['shipping_address'])

        shipping_id = None
        if not is_billing_delivery_same and record['shipping_address']:
            shipping_id = create_address(record['shipping_address'])

        billing_partner = self.env['res.partner'].browse(billing_id)
        billing_partner.type = 'invoice'

        partner_update_data = {
            'city': billing_partner.city,
            'country_id': billing_partner.country_id.id,
            'zip': billing_partner.zip,
            'phone': billing_partner.phone,
            'mobile': billing_partner.mobile,
            'street': billing_partner.street,
            'street2': billing_partner.street2,
        }
        if billing_partner.company:
            partner_update_data.update({'is_company': True,
                                        'company': False,
                                        'name': billing_partner.company,
                                        'consider_as_company': True, })
        elif not standard_import:
            partner_update_data.update({
                'is_company': False,
                'consider_as_company': False
            })

        partner_binding.write(partner_update_data)
        shipping_partner = self.env['res.partner'].browse(shipping_id)
        if shipping_id:
            shipping_partner.type = 'delivery'
        else:
            billing_partner.type = 'contact'
        # shipping_partner.with_context(skip_address_sync_from_parent=True).write({'active': False})
        # billing_partner.with_context(skip_address_sync_from_parent=True).write({'active': False})

        self.partner_id = partner.id
        self.partner_invoice_id = billing_id
        self.partner_shipping_id = shipping_id or billing_id

    def _import_dependencies(self):
        record = self.magento_record
        self._import_addresses()

        product_binder = self.binder_for('magento.product.product')
        for line in record.get('items', []):
            _logger.debug('line: %s', line)
            if 'product_id' in line:
                if not product_binder.to_internal(line['product_id']):
                    raise Exception(_('Product with magento_id=%s does not exists in Odoo!' % (line['product_id'])))


class SaleOrderImportMapper(Component):
    _name = 'magento.sale.order.mapper'
    _inherit = 'magento.sale.order.mapper'
    _apply_on = 'magento.sale.order'

    @mapping
    def fiscal_position(self, record):
        res = {}

        billing_address = record.get('billing_address', False)

        if billing_address and billing_address.get('country_id', False):
            country_code = billing_address['country_id']
            country = self.env['res.country'].search([('code', '=', country_code)])

            if country:
                for line in self.backend_record.fiscal_mapping_ids:
                    if line.country_id.id == country.id:
                        res['fiscal_position'] = line.fiscal_position_id.id
                        break

        return res


class SaleOrderLineImportMapper(Component):
    _name = 'magento.sale.order.line.mapper'
    _inherit = 'magento.sale.order.line.mapper'
    _apply_on = 'magento.sale.order.line'

    @mapping
    def tax(self, record):
        tax_percent = record.get('tax_percent', False)
        if tax_percent:
            for tax_mapping in self.backend_record.tax_mapping_ids:
                if tax_mapping.magento_tax_percent == float(tax_percent):

                    res_tax = tax_mapping.tax_id
                    fiscal_position_data = self.component(usage='import.mapper',
                                                          model_name='magento.sale.order').fiscal_position(record)
                    if fiscal_position_data:
                        fiscal_pos_id = int(fiscal_position_data['fiscal_position'])
                        fiscal_position = self.env['account.fiscal.position'].browse(fiscal_pos_id)
                        res_tax = fiscal_position.map_tax(tax_mapping.tax_id)
                    return {'tax_id': [(6, 0, res_tax.ids)]}
        return {}
