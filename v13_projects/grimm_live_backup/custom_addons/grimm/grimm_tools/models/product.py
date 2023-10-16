#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  config.py
#
#  Copyright 2015 D.H. Bahr <dhbahr@gmail.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#

from odoo import api, fields, models, tools, _
from datetime import datetime
from odoo.tools import float_compare, float_round, float_is_zero, pycompat
from odoo.exceptions import UserError
import csv
from bs4 import BeautifulSoup
import base64
from io import StringIO
import logging
import ast

_logger = logging.getLogger(__name__)

class ProductPackage(models.Model):
    _name = 'product.package'
    _description = 'Product package'

    name = fields.Char(string='Name',required=True)
    qty_no = fields.Integer(string='No of Package',required=True)

class StockPicking(models.Model):
    _inherit = "stock.picking"

    print_label = fields.Boolean("Print Label", default=False,
                                 help="If it is True it will print label after validating incomming shipment.")

    def action_done(self):
        res = super(StockPicking, self).action_done()
        for pick in self:
            if pick.picking_type_id.sequence_id.id == 15 and pick.print_label:
                pick.brother_print()
        return res

    def brother_print(self):
        label_printer = self.env["label.printer"].search([], limit=1)
        if label_printer:
            label_printer.print_label('grimm_tools.receipt_label_print_template', self.id, rotate=0)

class StockLocation(models.Model):
    _inherit = "stock.location"

    print_rotation = fields.Integer(string='Print Rotation', default=0, help="You can define degree for print location label e.g. 90 or 180")

    def brother_print(self):
        label_printer = self.env["label.printer"].search([], limit=1)
        if label_printer:
            label_printer.print_label('grimm_tools.location_receipt_label_print_template', self.id, rotate=self.print_rotation)

'''
#Odoo13Change Odoo13 removed _run_valuation method so comment below code
class StockMove(models.Model):
    _inherit = "stock.move"

    def _run_valuation(self, quantity=None):
        self.ensure_one()
        if self._is_in():
            valued_move_lines = self.move_line_ids.filtered(lambda ml: not ml.location_id._should_be_valued() and ml.location_dest_id._should_be_valued() and not ml.owner_id)
            valued_quantity = 0
            for valued_move_line in valued_move_lines:
                valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done, self.product_id.uom_id)

            # Note: we always compute the fifo `remaining_value` and `remaining_qty` fields no
            # matter which cost method is set, to ease the switching of cost method.
            vals = {}
            price_unit = self._get_price_unit()
            value = price_unit * (quantity or valued_quantity)
            vals = {
                'price_unit': price_unit,
                'value': value if quantity is None or not self.value else self.value,
                'remaining_value': value if quantity is None else self.remaining_value + value,
            }
            vals['remaining_qty'] = valued_quantity if quantity is None else self.remaining_qty + quantity

            if self.product_id.cost_method == 'standard':
                try:
                    prod_standard_price = self.product_id.standard_price
                except:
                    prod_standard_price = self.product_id.standard_price
                value = prod_standard_price * (quantity or valued_quantity)
                vals.update({
                    'price_unit': prod_standard_price,
                    'value': value if quantity is None or not self.value else self.value,
                })
            self.write(vals)
        elif self._is_out():
            valued_move_lines = self.move_line_ids.filtered(lambda ml: ml.location_id._should_be_valued() and not ml.location_dest_id._should_be_valued() and not ml.owner_id)
            valued_quantity = 0
            for valued_move_line in valued_move_lines:
                valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done, self.product_id.uom_id)
            self.env['stock.move']._run_fifo(self, quantity=quantity)
            if self.product_id.cost_method in ['standard', 'average']:
                curr_rounding = self.company_id.currency_id.rounding
                try:  # Added try  catch to resolved get standard price issue
                    value = -float_round(self.product_id.standard_price * (valued_quantity if quantity is None else quantity), precision_rounding=curr_rounding)
                except:
                    value = -float_round(self.product_id.standard_price * (valued_quantity if quantity is None else quantity), precision_rounding=curr_rounding)
                self.write({
                    'value': value if quantity is None else self.value + value,
                    'price_unit': value / valued_quantity,
                })
        elif self._is_dropshipped() or self._is_dropshipped_returned():
            curr_rounding = self.company_id.currency_id.rounding
            if self.product_id.cost_method in ['fifo']:
                price_unit = self._get_price_unit()
                # see test_dropship_fifo_perpetual_anglosaxon_ordered
                self.product_id.standard_price = price_unit
            else:
                try:
                    price_unit = self.product_id.standard_price
                except:
                    price_unit = self.product_id.standard_price
            value = float_round(self.product_qty * price_unit, precision_rounding=curr_rounding)
            # In move have a positive value, out move have a negative value, let's arbitrary say
            # dropship are positive.
            self.write({
                'value': value if self._is_dropshipped() else -value,
                'price_unit': price_unit if self._is_dropshipped() else -price_unit,
            })
'''
class BarcodeProduct(models.Model):
    _name = 'barcode.product'
    _description = 'Allowed product for Inventory scan.'

    name = fields.Char(string='Name',required=True)
    product_ids = fields.Many2many('product.product', string='Allowed Product')

class ProductProduct(models.Model):
    _inherit = "product.product"

    def _get_context_product(self, product, user):
        pricelist_id = user.company_id.pricelist_id
        product = product.with_context(
            quantity=1,
            pricelist=pricelist_id.id,
            uid=user.id
        )
        return product

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        name = name.strip() # As per request from Andre trimmed name for searching convenient
        return super(ProductProduct, self).name_search(name, args, operator, limit)

    def _check_shopware_price(self):
        csv_file = StringIO()
        csv.writer(csv_file).writerow(["Product ID", "Internal Ref", "Channel", "List Price", "Shop Price"])
        self._cr.execute("SELECT openerp_id from shopware_product_template")
        sql_result = self._cr.fetchall()
        prod_ids = [res[0] for res in sql_result]
        shopware_user = self.env["res.users"].search([('login', '=', 'shopware@grimm-gastrobedarf.de')], limit=1)
        prod_len = len(prod_ids)
        for index,prod_id in enumerate(prod_ids):
            try:
                product = self.env["product.template"].browse(prod_id)
                _logger.info("Processing shopware price %s === %s "%(prod_len,index))
            except:
                product = False
            if product and product.active:
                rrp_price = round(product.rrp_price, 2)
                if not shopware_user:
                    shopware_user = self.env["res.users"].browse(self._context.get("uid", self.env.user.id))
                product = self._get_context_product(product, shopware_user)
                shopware_price = round(product.calculated_magento_price, 2)
                if rrp_price < shopware_price:
                    csv.writer(csv_file).writerow([str(product.id), str(product.default_code), "Shopware", str(rrp_price), str(shopware_price)])
        if csv_file:
            self.send_price_diff_alarm_email(csv_file)

    def _check_magento_price(self):
        return True
        self._cr.execute("SELECT openerp_id from magento_product_product")
        sql_result = self._cr.fetchall()
        prod_ids = [res[0] for res in sql_result]
        csv_file = StringIO()
        csv.writer(csv_file).writerow(["Product ID", "Internal Ref", "Channel", "List Price", "Shop Price"])
        magento_user = self.env["res.users"].search([('login', '=', 'magento@grimm-gastrobedarf.de')],limit=1)
        prod_len = len(prod_ids)
        for index,prod_id in enumerate(prod_ids):
            try:
                product = self.env["product.product"].browse(prod_id)
                _logger.info("Processing magento price %s === %s " % (prod_len, index))
            except:
                product = False
            if product and product.active:
                rrp_price = round(product.rrp_price,2)
                if not magento_user:
                    magento_user = self.env["res.users"].browse(self._context.get("uid", self.env.user.id))
                product = self._get_context_product(product, magento_user)
                magento_price = round(product.calculated_magento_price,2)
                if rrp_price < magento_price:
                    csv.writer(csv_file).writerow([str(product.id), str(product.default_code), "Magento", str(rrp_price), str(magento_price)])

        if csv_file:
            self.send_price_diff_alarm_email(csv_file)

    @api.model
    def send_price_diff_alarm_email(self, csv_file):
        vals = {'email_from': 'office@grimm-gastrobedarf.de',
                'email_to': self.env["ir.config_parameter"].get_param("price.diff.alarm.emails",default="d.suthar@grimm-gastrobedarf.de"),
                'body_html': "<pre>Hallo liebe Kollegen,<br /><br />Please find attached file with details.</pre>", 'type': 'email','subject': 'Price Alarm difference'}
        mail = self.env['mail.mail'].create(vals)

        datas = base64.b64encode(csv_file.getvalue().encode('utf-8'))
        attachment = self.env['ir.attachment'].create(
            {'name': 'price_difference_alarm', 'type': 'binary', 'datas': datas, 'extension': '.csv',
             'datas_fname': 'price_alarm.csv'})
        mail.attachment_ids = [(4, attachment.id)]
        mail.send()
        #attachment.unlink()



    def _select_seller(self, partner_id=False, quantity=0.0, date=None, uom_id=False, params=False):
        self.ensure_one()
        # Inherited this method to check condition if date is False
        if date is None or not date:
            date = fields.Date.context_today(self)
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        res = self.env['product.supplierinfo']
        sellers = self.seller_ids
        if self.env.context.get('force_company'):
            sellers = sellers.filtered(
                lambda s: not s.company_id or s.company_id.id == self.env.context['force_company'])
        # p_id = sellers.mapped("product_id.id") # If supplier for variant then we need selected sellers.
        # if p_id:
        #     sellers = sellers.sorted(key=lambda r: r.product_id, reverse=True)
        for seller in sellers:
            # Set quantity in UoM of seller
            quantity_uom_seller = quantity
            if quantity_uom_seller and uom_id and uom_id != seller.product_uom:
                quantity_uom_seller = uom_id._compute_quantity(quantity_uom_seller, seller.product_uom)

            if seller.date_start and seller.date_start > date:
                continue
            if seller.date_end and seller.date_end < date:
                continue
            if partner_id and seller.name not in [partner_id, partner_id.parent_id]:
                continue
            # if float_compare(quantity_uom_seller, seller.min_qty, precision_digits=precision) == -1:
            #    continue
            if seller.product_id and seller.product_id.id != self.id:
               continue

            res |= seller
            break
        return res


class ProductTemplate(models.Model):
    _inherit = "product.template"

    is_package = fields.Boolean("Is package Product ?")
    package_id = fields.Many2one('product.package', string='Package')



    def grimm_action_view_sales(self):
        self.ensure_one()
        action = self.env.ref('grimm_tools.grimm_action_product_sale_list')
        product_ids = self.with_context(active_test=False).product_variant_ids.ids

        return {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'view_mode': action.view_mode,
            'target': action.target,
            'context': "{'default_product_id': " + str(product_ids[0]) + "}",
            'res_model': action.res_model,
            'domain': [('state', 'in', ['sale', 'done']), ('product_id.product_tmpl_id', '=', self.id)],
        }

    @api.depends('product_variant_ids', 'product_variant_ids.standard_price')
    def _compute_standard_price(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            try:
                template.standard_price = template.product_variant_ids.standard_price
            except:
                template.standard_price = template.product_variant_ids.standard_price
        for template in (self - unique_variants):
            template.standard_price = 0.0

    def grimm_remove_all_bindings(self, active_ids=False):
        if active_ids:
            for prod in self.browse(active_ids):
                prod.remove_bindings(prod, 'all')

    def write(self, vals):
        if isinstance(vals, dict):
            if "description" in vals.keys():
                if vals.get("description",False):
                    vals["description"] = self._remove_unwanted_tag(html_text=vals.get("description"))
        res = super(ProductTemplate, self).write(vals)
        return res

    def create(self, vals):
        if isinstance(vals, dict):
            if "description" in vals.keys():
                if vals.get("description",False):
                    vals["description"] = self._remove_unwanted_tag(html_text=vals.get("description"))
        res = super(ProductTemplate, self).create(vals)
        return res

    def _remove_unwanted_tag(self, valid_tags = False, html_text=False):
        if self.env.company.product_desc_validation:
            if not valid_tags:
                valid_tags = ast.literal_eval(self.env.company.valid_tags)
            soup = BeautifulSoup(html_text, features="lxml")
            remove_attributes = ast.literal_eval(self.env.company.remove_attrs)
            for tag in soup():
                for attribute in remove_attributes:
                    del tag[attribute]
            for match in soup.findAll():
                if valid_tags and match.name not in valid_tags:
                    match.replaceWithChildren()
            return str(soup)
        return html_text



class ResCompany(models.Model):
    _inherit = 'res.company'

    fax = fields.Char(string='Fax')
    pricelist_id = fields.Many2one("product.pricelist", string="Shop Pricelist", help="This is starting point to calculate shop price.")

class QueueJob(models.Model):
    _inherit = 'queue.job'

    message_info = fields.Html(string="Message Info", compute='_compute_message_info')
    rec_link = fields.Char(string="Record Link", compute='_compute_rec_link')

    def related_action_shopware6_link(self, component_usage="binder"):
        """ Open a form view with the unwrapped record.

        For instance, for a job on a ``shopware6.sale.order``,
        it will open a ``product.product`` form view with the unwrapped
        record.

        :param component_usage: base component usage to search for the binder
        """
        self.ensure_one()
        model_name = self.model_name
        if self.args:
            if len(self.args) > 1:
                shopware6_id = self.args[1]
                binding_record = self.env[model_name].sudo().search([('shopware6_id', '=', shopware6_id)])
                if binding_record and binding_record.openerp_id:
                    action = {
                        "name": _("Related Record"),
                        "type": "ir.actions.act_window",
                        "view_type": "form",
                        "view_mode": "form",
                        "res_model": binding_record.openerp_id._name,
                        "res_id": binding_record.openerp_id.id,
                    }
                    return action
        return None

    def _message_failed_job(self):
        """Return a message which will be posted on the job when it is failed.

        It can be inherited to allow more precise messages based on the
        exception informations.

        If nothing is returned, no message will be posted.
        """
        self.ensure_one()
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        database_name = self._cr.dbname
        rec_link = '%s/web?db=%s#id=%s&view_type=form&model=%s' % (base_url, database_name, self.id, "queue.job")

        return _(
            "<a href='%s' style='background-color: #009EE3; border-radius: 15px;color: white;padding: 20px 34px;text-align: center;text-decoration: none;display: inline-block;cursor: pointer;'>Open Job</a> <br/><br/>Something bad happened during the execution of the job. "
            "More details in the 'Exception Information' section."%rec_link
        )

    def _compute_rec_link(self):
        for record in self:
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            database_name = self._cr.dbname
            record.rec_link = '%s/web?db=%s#id=%s&view_type=form&model=queue.job' % (base_url, database_name, self.id)

    def _compute_message_info(self):
        for record in self:
            delayed = self._get_time_difference()
            record.message_info = self._get_suitable_msg(delayed)

    def _get_recipients_list(self):
        '''
        Return recipients list which configured in system parameter.
        :return: list
        '''
        email_list = self.env["ir.config_parameter"].get_param("blocked.job.emails")
        if not email_list:
            email_list = "d.suthar@grimm-gastrobedarf.de,m.liesegang@grimm-gastrobedarf.de" # If no email(s) configured then return Dipak's and Marco's email as default.
        return email_list

    def _get_suitable_msg(self,delayed):
        '''
        Based on delayed minutes will return suitable message for email
        :param delayed:
        :return: string
        '''
        if delayed > 5 and delayed < 30:
            return  _(
                "Below job has been blocked since more than 5 minutes in job queue. So this job is automatic added in requeue.<br/><br/><strong>%s</strong><br/></p>" % (
                    self.name))
        if delayed > 30:
            return _(
                "Below job has been blocked since more than 30 minutes in job queue. Scheduler has already added this job in requeue, if you receive email for same job then please contact IT team <br/><br/><strong>%s</strong><br/> Please add this job in requeue or do needful.</p>" % (
                    self.name))


    def _get_time_difference(self):
        '''
        Calculate difference with current date time and return delayed info
        :param create_date:
        :return: Integer delayed minutes
        '''
        current_date = fields.Datetime.now() #(datetime.strptime(str(fields.Datetime.now()), '%Y-%m-%d %H:%M:%S'))
        if self.date_started:
            create_date = self.date_started #(datetime.strptime(str(self.date_started), '%Y-%m-%d %H:%M:%S'))
        else:
            create_date = self.date_created #(datetime.strptime(str(self.date_created), '%Y-%m-%d %H:%M:%S'))
        return (current_date - create_date).total_seconds() / 60


    @api.model
    def _check_running_crone_job(self):
        '''
        This method will be called from cron job.
        :return:
        '''
        current_job = self.env['queue.job'].search([('state','in',['enqueued','started'])])
        template = self.env.ref('grimm_tools.blocked_message_email_template', raise_if_not_found=False)
        email_list = self._get_recipients_list()
        template.email_to = email_list
        for job in current_job:
            delayed = job._get_time_difference()
            if delayed > 5 and delayed < 30:
                template.subject = _("Blocked job added in Requeue %s" % (job.name))
                if template:
                    template.sudo().send_mail(job.id, force_send=True)
                job.requeue()
            if delayed > 30:
                template.subject = _("Blocked job in Queue %s" % (job.name))
                if template:
                    template.sudo().send_mail(job.id, force_send=True)
                job.requeue()

class AccountInvoiceLine(models.Model):
    _inherit = 'account.move.line'

    # Added code if user manually change tax then we also need to change account.
    @api.onchange('tax_ids')
    def _onchange_taxes(self):
        selected_taxes = self.tax_ids.ids
        if set([12,13,14,15]) & set(selected_taxes):
            src_account = self.env['account.fiscal.position.account'].search([('position_id', '=', 16),('account_dest_id', '=', self.account_id.id)])
            if src_account:
                self.account_id = src_account.account_src_id.id
        elif set([27,28,29,30]) & set(selected_taxes):
            fpos = self.env["account.fiscal.position"].sudo().browse(16)
            accounts = self.product_id.product_tmpl_id.get_product_accounts(fpos)
            if self.move_id.type in ('out_invoice', 'out_refund'):
                self.account_id = accounts['income'].id
            else:
                self.account_id = accounts['expense'].id

    def _set_taxes(self):
        """ Used in on_change to set taxes and price."""
        if self.invoice_id.type in ('out_invoice', 'out_refund'):
            taxes = self.product_id.taxes_id or self.account_id.tax_ids
        else:
            taxes = self.product_id.supplier_taxes_id or self.account_id.tax_ids

        # Keep only taxes of the company
        company_id = self.company_id or self.env.user.company_id
        taxes = taxes.filtered(lambda r: r.company_id == company_id)

        self.invoice_line_tax_ids = fp_taxes = self.invoice_id.fiscal_position_id.map_tax(taxes, self.product_id, self.invoice_id.partner_id)

        fix_price = self.env['account.tax']._fix_tax_included_price
        if self.invoice_id.type in ('in_invoice', 'in_refund'):
            prec = self.env['decimal.precision'].precision_get('Product Price')
            if not self.price_unit or float_compare(self.price_unit, self.product_id.standard_price, precision_digits=prec) == 0:
                self.price_unit = fix_price(self.product_id.standard_price, taxes, fp_taxes)
                self._set_currency()
        else:
            self.price_unit = fix_price(self.product_id.lst_price, taxes, fp_taxes)
            ### Committed code to set magento price while creation of Invoice. (OD-715)
            if self.env.user.company_id.id == 1:
                self.price_unit = fix_price(self.product_id.calculated_magento_price, taxes, fp_taxes)
            self._set_currency()