# -*- coding: utf-8 -*-
# © 2013-2017 Guewen Baconnier,Camptocamp SA,Akretion
# © 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from datetime import datetime, timedelta
from odoo import models, fields, api
from odoo.addons.component.core import Component
import logging
from datetime import datetime
from datetime import timedelta
_logger = logging.getLogger(__name__)
from odoo.addons.component_event import skip_if
from odoo.addons.component.core import Component
from odoo.addons.queue_job.job import job, related_action


class CategoryRelatedProduct(models.Model):
    _name = 'category.related.product'
    _inherit = ['shopware6.binding']
    _description = 'Shopware6 Category Related Products'
    _parent_name = 'backend_id'

    category_id = fields.Many2one('product.category',string="Product Category")
    product_id = fields.Many2one('product.product', string="Product")
    name = fields.Char(string='Product Name', compute='_compute_prod_name')
    product_tmpl_id = fields.Many2one('product.template', string="Product")
    type = fields.Selection([
        ('pp', 'Product Product'),
        ('pt', 'Product Template')
    ], string='Type', default='pp',
        help="Describes the product type variant product or template product.")
    sequence = fields.Integer('Position', default=0)
    backup_seq = fields.Integer('Back-up Position', default=0)
    position = fields.Integer('Position', related='sequence', readonly=False)
    currency_id = fields.Many2one('res.currency', string='Currency')
    calculated_magento_price = fields.Monetary(string='Shop Price', help='Calculated Preis for Magento')
    image_1920 = fields.Image("Image",related='product_id.image_1920')

    _sql_constraints = [('category_product_unique', 'unique (product_id, category_id)',
                         'You can not assign same product twice.!')]

    def _compute_prod_name(self):
        self.name = ""
        for this in self:
            if this.product_id:
                this.name = "[%s] %s"%(this.product_id.default_code,this.product_id.name)
                this.calculated_magento_price = this.product_id.calculated_magento_price
            elif this.product_tmpl_id:
                this.name = "[%s] %s"%(this.product_tmpl_id.base_default_code or this.product_tmpl_id.default_code,this.product_tmpl_id.name)
                this.calculated_magento_price = this.product_tmpl_id.calculated_magento_price

class Shopware6CategoryRelatedProductAdapter(Component):
    _name = 'shopware6.category.related.product.adapter'
    _inherit = 'shopware6.adapter'
    _apply_on = 'category.related.product'

    _shopware_uri = 'api/swpa-sort/apply'

    def write(self, id, data):
        """ Update category on the Shopware system """
        return self._call('POST', '%s' % (self._shopware_uri), data)

# class CategoryRelatedProductListener(Component):
#     _name = 'category.related.product.listener'
#     _inherit = 'base.connector.listener'
#     _apply_on = ['category.related.product']
#
#     @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
#     def on_record_write(self, record, fields=None):
#         print("Calling update method for category.related.product ===> ", record, fields)
#         if 'sequence' in fields:
#             record.export_record(fields=fields)
        # for shopware_bind in record.shopware6_brand_ids:
        #     shopware_bind.with_delay().export_record(fields=fields)

class Shopware6ProductCategory6Listener(Component):
    _name = 'shopware6.product.category.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['product.category']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        if record.shopware6_bind_ids and 'related_product_ids' in fields:
            for p_id in record.related_product_ids:
                # p_id.with_delay().export_record(fields=fields)
                p_id.with_delay(description="Products position update job for %s category."%record.name or "").export_record(fields=fields)
                break


class ProductCategory(models.Model):
    _inherit = 'product.category'

    related_product_ids = fields.One2many('category.related.product', 'category_id', string="Related Products")
    compute_field = fields.Char(string='Compute Field', compute='_compute_field_test')
    sort_method = fields.Selection([
        ('auto', 'Automatic'),
        ('manual', 'Manual')
    ], string='Sort Method', required=True, default='manual',
        help="Sort on Shopware. Auto = Based on sales count, Manual = Based on manual sorting method.")

    active = fields.Boolean(
        string="Active",
        default=True,
        help="If unchecked, it will allow you to hide the "
             "product category without removing it.",
    )

    @api.onchange('sort_method')
    def onchange_sort_method(self):
        product_ids = self.mapped("related_product_ids.product_id.id")
        sort_seq = self._get_sequence_by_sales(product_ids)
        if self.sort_method == 'auto':
            for product in self.related_product_ids:
                product._origin.write({'backup_seq': product.sequence,
                                       'sequence': sort_seq.get(product.product_id.id, len(sort_seq) + 10)})
                try:
                    product.write({'backup_seq': product.sequence,
                                           'sequence': sort_seq.get(product.product_id.id, len(sort_seq) + 10)})
                except:
                    pass

        else:
            for product in self.related_product_ids:
                product._origin.write({'sequence': product.backup_seq})
                try:
                    product.write({'sequence': product.backup_seq})
                except:
                    pass

    def _compute_field_test(self):
        for res in self:
            res.compute_field = ""
            res.reload_assigned_products()

    def _get_sequence_by_sales(self, product_ids=[]):
        if product_ids:
            product_ids.append(0)
            qry_str = "select product_id,sum(product_uom_qty) from sale_order_line where product_id in %s and order_id in (select id from sale_order where team_id in (2) and state in ('sale', 'done')) group by product_id;"%(tuple(product_ids),)
            self._cr.execute(qry_str)
            prod_seq = {}
            [prod_seq.update({x[0]:x[1]}) for x in self._cr.fetchall()]
            sort_seq = {}
            for index, w in enumerate(sorted(prod_seq, key=prod_seq.get, reverse=True)):
                sort_seq[w] = index+1
            return sort_seq

    def _add_template_category(self):
        self._cr.execute(
            "select product_template_id from product_template_product_category_rel where product_template_id in (select product_tmpl_id from product_product where shopware_active='t' and active='t') and  product_category_id=%s" % (self._origin.id))
        product_ids = [x[0] for x in self._cr.fetchall()]
        if product_ids:
            self._cr.execute("select product_tmpl_id from category_related_product where product_tmpl_id is not null and category_id=%s" % (self._origin.id))
            exist_product_ids = [x[0] for x in self._cr.fetchall()]
            need_to_delete = [p_id for p_id in exist_product_ids if p_id not in product_ids]
            self._cr.execute("select max(sequence) from category_related_product where category_id=%s" % (self._origin.id))
            try:
                max_sequence = int([x[0] for x in self._cr.fetchall()][0])
            except:
                max_sequence = 0
            if need_to_delete:
                need_to_delete.append(0)
                self._cr.execute("delete from category_related_product where product_id is null and category_id=%s and product_tmpl_id in %s;" % (self._origin.id, tuple(need_to_delete)))
            self._cr.execute("commit;")
            if not all(p_id in exist_product_ids for p_id in product_ids):
                for p_id in product_ids:
                    max_sequence += 1
                    backends = self.env['shopware6.backend'].search([])
                    for backend in backends:
                        try:
                            self._cr.execute("insert into category_related_product (product_tmpl_id,category_id,sequence,backend_id,type) VALUES (%s,%s,%s,%s,'pt')" % (p_id, self._origin.id, max_sequence, backend.id))
                        except:
                            pass

    def reload_assigned_products(self):
        self.ensure_one()
        self._cr.execute("select product_product_id from product_category_product_product_rel where product_product_id in (select id from product_product where shopware_active='t' and active='t') and  product_category_id=%s" % (self._origin.id))
        product_ids = [x[0] for x in self._cr.fetchall()]
        self._cr.execute("select product_id from category_related_product where product_id is not null and category_id=%s" % (self._origin.id))
        exist_product_ids = [x[0] for x in self._cr.fetchall()]
        need_to_delete = [p_id for p_id in exist_product_ids if p_id not in product_ids]

        self._cr.execute("select max(sequence) from category_related_product where category_id=%s" % (self._origin.id))
        try:
            max_sequence = int([x[0] for x in self._cr.fetchall()][0])
        except:
            max_sequence = 0
        if need_to_delete:
            need_to_delete.append(0)
            self._cr.execute("delete from category_related_product where product_tmpl_id is null and category_id=%s and product_id in %s;" % (self._origin.id, tuple(need_to_delete)))
        self._cr.execute("commit;")
        if not all(p_id in exist_product_ids for p_id in product_ids):
            for p_id in product_ids:
                max_sequence += 1
                backends = self.env['shopware6.backend'].search([])
                for backend in backends:
                    try:
                        self._cr.execute("insert into category_related_product (product_id,category_id,sequence,backend_id,type) VALUES (%s,%s,%s,%s,'pp')" % (p_id, self._origin.id, max_sequence, backend.id))
                    except:
                        pass
        self._add_template_category() # Adding template for category
        if self.sort_method == 'auto':
            product_ids = self.mapped("related_product_ids.product_id.id")
            sort_seq = self._get_sequence_by_sales(product_ids)
            for product in self.related_product_ids:
                product.sequence = sort_seq.get(product.product_id.id, len(sort_seq) + 10)
        return True