# -*- coding: utf-8 -*-

from odoo import fields, models, api, tools
from datetime import datetime, timedelta


class CrmProfit(models.Model):
    _name = 'crm.profit'
    _description = "CRM Profitable Customers/Vendors"
    _auto = False
    _order = 'order_freq desc'

    order_freq = fields.Float(string='Order Frequency per Year', readonly=True)
    margin = fields.Float(string='Margin', readonly=True)
    no_of_so = fields.Integer(string='No. of Sale Orders', readonly=True)
    profit = fields.Float(string='AVG Profit (in %)', readonly=True)
    total_amount = fields.Float(string='Total Amount', readonly=True)
    partner_id = fields.Many2one(comodel_name='res.partner', string='Partner', readonly=True)
    is_vendor = fields.Integer(string='Is a Vendor', related='partner_id.supplier_rank', readonly=True)
    categ_id = fields.Many2one(comodel_name='product.category', string='Category ID', readonly=True)
    product_id = fields.Many2one(comodel_name='product.product', string='Product', readonly=True)
    product_brand_id = fields.Many2one(comodel_name='grimm.product.brand', string='Brand ID')
    sale_order_id = fields.Many2one(comodel_name='sale.order', string='Sale Order')

    def init(self):
        yr_ref = datetime.now().strftime('%Y')
        tools.drop_view_if_exists(self.env.cr, self._table)
        query = """CREATE OR REPLACE VIEW %s AS (
            WITH crm_profit_partner AS (
                SELECT so.partner_id, COUNT(*) as no_of_so, SUM(so.amount_total) as total_amount, SUM(so.margin) as margin, SUM(so.margin)/SUM(so.amount_total) as profit, 
                date_trunc('month', so.date_order), rp.supplier_rank as is_vendor, pp.id as product_id, so.id as sale_order_id, pt.categ_id, pt.product_brand_id
                FROM sale_order as so
                INNER JOIN sale_order_line AS sol on so.id = sol.order_id
                INNER JOIN product_product AS pp on sol.product_id = pp.id
                INNER JOIN product_template AS pt on pp.product_tmpl_id = pt.id
                INNER JOIN res_partner rp on so.partner_id = rp.id
                WHERE so.margin > 0 AND so.amount_total > 0 AND so.date_order > '%s' AND so.state='done' 
                GROUP BY so.partner_id, date_trunc('month', so.date_order), rp.supplier_rank, pp.id, so.id, pt.categ_id, pt.product_brand_id)
                SELECT ROW_NUMBER() OVER() as id, crp.partner_id, SUM(crp.no_of_so) as no_of_so, SUM(crp.total_amount) as total_amount, SUM(crp.margin) as margin, SUM(crp.profit)/12*100 as profit, SUM(crp.no_of_so)/12 as order_freq,
                crp.is_vendor, crp.product_id, crp.sale_order_id, crp.categ_id, crp.product_brand_id
                FROM crm_profit_partner as crp
                GROUP BY crp.partner_id, crp.is_vendor, crp.product_id, crp.sale_order_id, crp.categ_id, crp.product_brand_id
        )
        """ % (self._table, str(int(yr_ref) - 1) + '-01-01 00:00:00')

        self.env.cr.execute(query)

    def send_personalised_email(self, active_ids=False, context=False):
        return {
            "type": "ir.actions.act_window",
            "res_model": "mail.mass_mailing",
            "views": [[self.env.ref('mass_mailing.view_mail_mass_mailing_form').id, "form"]],
            "context": {'default_mailing_model_id': 786},
            "target": "new",
        }
