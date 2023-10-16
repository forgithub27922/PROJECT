# -*- coding: utf-8 -*-


from odoo import models, fields, api, tools


class SalePurchaseReport(models.Model):
    _name = "sale.purchase.report"
    _description = "Sales Purchases Statistics"
    _auto = False
    _rec_name = 'date'
    _order = 'date desc'

    date = fields.Datetime(string='Date Order', readonly=True)
    product_id = fields.Many2one(comodel_name='product.product', string='Product', readonly=True)
    sale_id = fields.Many2one(comodel_name='sale.order', string='Sale Order', readonly=True)
    partner_id = fields.Many2one(comodel_name='res.partner', string='Customer', readonly=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', readonly=True)
    purchase_id = fields.Many2one(comodel_name='purchase.order', string='Purchase Order', readonly=True)
    supplier_id = fields.Many2one(comodel_name='res.partner', string='Supplier', readonly=True)
    p_property_account_payable_id = fields.Many2one(comodel_name='account.account', string='Supplier Credit Account',
                                                    readonly=True)
    user_id = fields.Many2one(comodel_name='res.users', string='Sale Person', readonly=True)
    team_id = fields.Many2one(comodel_name='crm.team', string='Sale Team', readonly=True)
    categ_id = fields.Many2one(comodel_name='product.category', string='Category', readonly=True)
    sale_qty = fields.Float(string='Sale Quantity', readony=True)
    purchase_qty = fields.Float(string='Purchase Quantity', readony=True)
    sale_subtotal = fields.Float(string='Sale Subtotal', readony=True)
    purchase_subtotal = fields.Float(string='Purchase Subtotal', readony=True)
    marge_subtotal = fields.Float(string='Marge Subtotal', readony=True)
    state = fields.Selection([
        ('draft', 'Draft Quotation'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Sales Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True)
    po_state = fields.Selection([('draft', 'Draft RFQ'),
                                 ('sent', 'RFQ Sent'),
                                 ('to approve', 'To Approve'),
                                 ('purchase', 'Purchase Order'),
                                 ('done', 'Done'),
                                 ('cancel', 'Cancelled')
                                 ], string='Status', readonly=True)

    def _select(self):
        select_str = """
            WITH currency_rate as (%s)
             SELECT 
             LEAST(min(st.id), min(pt.pol_id)) AS id,
                    st.product_id as product_id,
                    st.so_id AS sale_id,
                    st.date_order AS date,
                    st.partner_id as partner_id,
                    st.company_id AS company_id,
                    pt.po_id as purchase_id,
                    pt.supplier_id AS supplier_id,
                    sum(DISTINCT st.product_uom_qty) as sale_qty,
                    sum(DISTINCT pt.product_qty) as purchase_qty,
                    sum(DISTINCT st.price_total / COALESCE(cr.rate, 1.0)) as sale_total,
                    sum(DISTINCT st.price_subtotal / COALESCE(cr.rate, 1.0)) as sale_subtotal,
                    sum(DISTINCT pt.price_total / COALESCE(cr.rate, 1.0)) as purchase_total,
                    sum(DISTINCT pt.price_subtotal / COALESCE(cr.rate, 1.0)) as purchase_subtotal,
                    (sum(DISTINCT st.price_subtotal / COALESCE(cr.rate, 1.0)) - sum(DISTINCT pt.price_subtotal / COALESCE(cr.rate, 1.0))) as marge_subtotal,
                    st.team_id as team_id,
                    st.user_id as user_id,
                    t.categ_id as categ_id,
                    st.state,
                    pt.state as po_state,
                    NULLIF(pt.property_account_payable_id[2], '')::int
                     as p_property_account_payable_id
        """ % self.env['res.currency']._select_companies_rates()
        return select_str

    def _from(self):
        from_str = """
(SELECT
        sol.id,
        sol.product_uom_qty,
        sol.product_id,
        sol.price_total,
        so.id AS so_id,
        so.name,
        so.date_order,
        so.pricelist_id,
        so.partner_id,
        so.user_id,
        so.company_id,
        sol.price_subtotal,
        so.team_id,
        so.state
      FROM sale_order_line AS sol
        JOIN sale_order AS so ON sol.order_id = so.id
        ) AS st
        
  JOIN (
         SELECT
           pol.id as pol_id,
           pol.product_id,
           pol.product_qty,
           pol.price_total,
           po.id         as po_id,
           po.origin,
           po.partner_id as supplier_id,
           pol.price_subtotal,
           po.state,
           CASE WHEN ip1.value_reference IS NOT NULL THEN regexp_split_to_array(ip1.value_reference, ',')
                WHEN ip2.value_reference IS NOT NULL THEN regexp_split_to_array(ip2.value_reference, ',')
                ELSE regexp_split_to_array(ip3.value_reference, ',')
            END
            AS property_account_payable_id
         FROM purchase_order_line AS pol
           JOIN purchase_order AS po ON pol.order_id = po.id
           JOIN res_partner AS rp ON rp.id = po.partner_id
           LEFT JOIN res_partner rp2 ON rp.parent_id = rp2.id
           LEFT JOIN ir_property AS ip1 
            ON ip1.name = 'property_account_payable_id' AND
               ip1.res_id = 'res.partner,' || rp.id
            LEFT JOIN ir_property AS ip2
            ON ip2.name = 'property_account_payable_id' AND
               ip2.res_id = 'res.partner,' || rp2.id
            LEFT JOIN ir_property AS ip3 
            ON ip3.name = 'property_account_payable_id' AND
               ip3.res_id IS NULL
        )
     AS pt ON st.product_id = pt.product_id AND st.name = pt.origin
  left join product_pricelist pp on (st.pricelist_id = pp.id)
   left join product_product p on (st.product_id=p.id)
                            left join product_template t on (p.product_tmpl_id=t.id)
     left join currency_rate cr on (cr.currency_id = pp.currency_id and
                        cr.company_id = st.company_id and
                        cr.date_start <= coalesce(st.date_order, now()) and
                        (cr.date_end is null or cr.date_end > coalesce(st.date_order, now())))
        """
        return from_str

    def _group_by(self):
        group_by_str = """
            GROUP BY st.product_id,
                    st.so_id,
                    pt.pol_id,
                    st.state,
                    pt.state,
                    st.date_order,
                    st.company_id,
                    t.categ_id,
                    st.user_id,
                    st.team_id,
                    st.partner_id,
                    pt.po_id,
                    pt.supplier_id,
                    pt.property_account_payable_id
        """
        return group_by_str

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        query = """CREATE or REPLACE VIEW %s as (
            %s
            FROM ( %s )
            
            %s
            )""" % (self._table, self._select(), self._from(), self._group_by())
        self.env.cr.execute(query)
