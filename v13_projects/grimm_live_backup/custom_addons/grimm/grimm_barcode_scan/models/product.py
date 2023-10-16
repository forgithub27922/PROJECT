# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    ean_number = fields.Char('EAN Number', related='product_variant_ids.ean_number', readonly=False)
    barcode = fields.Char('Barcode', related='product_variant_ids.barcode', readonly=True)
    is_photo_done = fields.Boolean('Is Photo Done ?', related='product_variant_ids.is_photo_done')
    photo_date = fields.Datetime('Photo taken date', related='product_variant_ids.photo_date')

class ProductProduct(models.Model):
    _inherit = 'product.product'

    is_photo_done = fields.Boolean("Is Photo Done ?", help="This value displays True if photo has been done.", track_visibility='onchange' )
    photo_date = fields.Datetime("Photo taken date", help="Date when photo has been taken.")
    ean_number = fields.Char('EAN Number', copy=False, help="International Article Number used for product identification.")
    barcode = fields.Char(
        'Barcode', copy=False, readonly=True,
        help="International Article Number used for product identification.")

    def write(self, vals):
        if isinstance(vals, dict):
            if "is_photo_done" in vals.keys():
                if vals.get("is_photo_done"):
                    vals["photo_date"] = fields.Datetime.now()
                else:
                    vals["photo_date"] = ""
        res = super(ProductProduct, self).write(vals)
        return res

    @api.model
    def create(self, vals):
        res = super(ProductProduct, self).create(vals)
        res.barcode = str(res.id).zfill(8)
        return res

    @api.model
    def get_all_products_by_barcode(self):
        moves = self.env['stock.move'].search_read(
            [('product_id.barcode', '!=', None),('product_id.type', '=', 'product')],
            ['product_id'], order='create_date DESC', limit=10000)
        product_ids = list(set(m['product_id'][0] for m in moves))
        # GRIMM added only one condition to not search consumable products.
        product_ids += self.env['product.product'].search(
            [('barcode', '!=', None), ('type', 'not in', ['service','consu'])], limit=10000).ids
        products = self.env['product.product'].browse(product_ids[:10000]).read(
            ['barcode', 'display_name', 'uom_id', 'tracking'])
        packagings = self.env['product.packaging'].search_read(
            [('barcode', '!=', None), ('product_id', '!=', None)],
            ['barcode', 'product_id', 'qty']
        )
        # for each packaging, grab the corresponding product data
        to_add = []
        to_read = []
        products_by_id = {product['id']: product for product in products}
        for packaging in packagings:
            if products_by_id.get(packaging['product_id']):
                product = products_by_id[packaging['product_id']]
                to_add.append(dict(product, **{'qty': packaging['qty']}))
            # if the product doesn't have a barcode, you need to read it directly in the DB
            to_read.append((packaging, packaging['product_id'][0]))
        products_to_read = self.env['product.product'].browse(list(set(t[1] for t in to_read))).sudo().read(
            ['display_name', 'uom_id', 'tracking'])
        products_to_read = {product['id']: product for product in products_to_read}
        to_add.extend([dict(t[0], **products_to_read[t[1]]) for t in to_read])
        return {product.pop('barcode'): product for product in products + to_add}

class MagentoInvoiceBuffer(models.Model):
    """
    """
    _name = 'magento.invoice.buffer'
    _description = 'Magento Invoice Buffer'

    magento_backend_id = fields.Integer(string='Magento Backend')
    openerp_id = fields.Integer(string='OpenERP ID')
    magento_order_id = fields.Integer(string='Magento Order ID')
    is_done = fields.Boolean(string='Is done?', default=False)

class MagentoShippmentBuffer(models.Model):
    """ Adds the ``one2many`` relation to the Magento bindings
    (``magento_bind_ids``)
    """
    _name = 'magento.shippment.buffer'
    _description = 'Magento Shipment Buffer'

    magento_backend_id = fields.Integer(string='Magento Backend')
    openerp_id = fields.Integer(string='OpenERP ID')
    magento_order_id = fields.Integer(string='Magento Order ID')
    is_done = fields.Boolean(string='Is done?', default=False)

    @api.model
    def _execute_magento_delivery_job(self):
        '''
        This method will be called from cron job.
        :return:
        '''
        delivery_jobs = self.env['magento.shippment.buffer'].search([('is_done', '=', False)])
        for job in delivery_jobs:
            self.env['magento.order.shipment'].create({
                'backend_id': job.magento_backend_id,
                'openerp_id': job.openerp_id,
                'magento_order_id': job.magento_order_id})
            job.is_done = True

        invoice_jobs = self.env['magento.invoice.buffer'].search([('is_done', '=', False)])
        for job in invoice_jobs:
            self.env['magento.account.invoice'].create({
                'backend_id': job.magento_backend_id,
                'openerp_id': job.openerp_id,
                'magento_order_id': job.magento_order_id})
            job.is_done = True



