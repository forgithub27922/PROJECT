# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools


class PurchaseReport(models.Model):
    _name = "grimm.purchase.report"
    _description = "Purchases Orders"
    _auto = False
    _order = 'date_order desc'

    date_order = fields.Datetime('Order Date', readonly=True, help="Date on which this document has been created")
    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    picking_type_id = fields.Many2one('stock.warehouse', 'Warehouse', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Vendor', readonly=True)
    delay_pass = fields.Float('Days to Deliver', digits=(16, 2), readonly=True, group_operator="avg")

    def init(self):
        tools.drop_view_if_exists(self._cr, 'grimm_purchase_report')
        # Previous code: extract(epoch from age(l.date_planned,s.date_order))/(24*60*60)::decimal(16,2) as delay_pass,
        # Execute the following function manually when you first upgrade this module
        self._cr.execute("""
        create or replace function weekdays_count_epoch_rep(fdate date, tdate date)
        returns bigint as
        $$
        SELECT CASE WHEN count(*)=0 THEN count(*) ELSE count(*)-1 END
        FROM generate_series(0, (fdate::date - tdate::date)) i
        WHERE date_part('dow', tdate::date + i) NOT IN (0,6)
        $$
        language sql;
        """)
        self._cr.execute("""
                create view grimm_purchase_report as (
                    WITH currency_rate as (%s)
                    select
                        min(l.id) as id,
                        spt.warehouse_id as picking_type_id,
                        s.partner_id as partner_id,
                        sm.product_id,
                        s.date_order,
                        extract(epoch from age(s.date_approve,s.date_order))/(24*60*60)::decimal(16,2) as delay,
                        cast(weekdays_count_epoch_rep(sp.date_done::date, s.po_date::date) as float8)::decimal(16,2) as delay_pass
                    from purchase_order_line l
                        join purchase_order s on (l.order_id=s.id)
                        join stock_picking sp on (s.name=sp.origin)
                        join res_partner partner on s.partner_id = partner.id
                            left join product_product p on (l.product_id=p.id)
                                left join product_template t on (p.product_tmpl_id=t.id)
                                LEFT JOIN ir_property ip ON (ip.name='standard_price' AND ip.res_id=CONCAT('product.product,',p.id) AND ip.company_id=s.company_id)
                        left join uom_uom u on (u.id=l.product_uom)
                        left join uom_uom u2 on (u2.id=t.uom_id)
                        left join stock_picking_type spt on (spt.id=s.picking_type_id)
                        left join account_analytic_account analytic_account on (l.account_analytic_id = analytic_account.id)
                        left join stock_move sm on (sp.id = sm.picking_id)
                    where sp.date_done is not null and s.po_date is not null and s.picking_type_id != 6
                    group by
                        s.partner_id,
                        s.date_approve,
                        l.date_planned,
                        s.date_order,
                        spt.warehouse_id,
                        s.po_date,
                        sp.date_done,
                        sm.product_id
                )
            """ % self.env['res.currency']._select_companies_rates())
