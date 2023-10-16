# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools


class SalePurchaseReport(models.Model):
    _name = "account.invoice.in_out.report"
    _description = "Out-In-Invoice Statistics"
    _auto = False
    _rec_name = 'date'
    _order = 'date desc'

    date = fields.Datetime(string='Date Order', readonly=True)
    invoice_date = fields.Date(string='Date Invoice', readonly=True)
    product_id = fields.Many2one(comodel_name='product.product', string='Product', readonly=True)
    sale_qty = fields.Float(string='Sale Quantity', readony=True)
    sale_subtotal = fields.Float(string='Sale Subtotal', readony=True)
    purchase_subtotal = fields.Float(string='Purchase Subtotal', readony=True)
    marge_subtotal = fields.Float(string='Marge Subtotal', readony=True)
    property_account_income_id = fields.Many2one(comodel_name='account.account', string='Account Income',
                                                 readonly=True)
    property_account_receivable_id = fields.Many2one(comodel_name='account.account', string='Account Debit',
                                                     readonly=True)
    property_account_expense_id = fields.Many2one(comodel_name='account.account', string='Account Expense',
                                                  readonly=True)
    property_payable_id = fields.Many2one(comodel_name='account.account', string='Account Credit',
                                          readonly=True)
    sale_invoice_id = fields.Many2one(comodel_name='account.move', string='Out Invoice', readonly=True)
    customer_id = fields.Many2one(comodel_name='res.partner', string='Customer', readonly=True)
    user_id = fields.Many2one(comodel_name='res.users', string='Sale Person', readonly=True)
    team_id = fields.Many2one(comodel_name='crm.team', string='Sale Team', readonly=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', readonly=True)
    sale_state = fields.Selection([('draft', 'Draft'),
                                   ('profoma', 'Profoma'),
                                   ('profoma2', 'Profoma2'),
                                   ('open', 'Open'),
                                   ('paid', 'Paid'),
                                   ('cancel', 'Cancelled'),
                                   ], string='Status Out Invoice', readonly=True)
    purchase_state = fields.Selection([('draft', 'Draft'),
                                       ('profoma', 'Profoma'),
                                       ('profoma2', 'Profoma2'),
                                       ('open', 'Open'),
                                       ('paid', 'Paid'),
                                       ('cancel', 'Cancelled'),
                                       ], string='Status In Invoice', readonly=True)
    purchase_qty = fields.Float(string='Purchase Quantity', readony=True)
    purchase_invoice_id = fields.Many2one(comodel_name='account.move', string='In Invoice', readonly=True)
    supplier_id = fields.Many2one(comodel_name='res.partner', string='Supplier', readonly=True)
    categ_id = fields.Many2one(comodel_name='product.category', string='Category', readonly=True)

    def _select(self):
        select_str = """
                    WITH currency_rate as (%s)
                    SELECT
  min(il.id)                                                                                        AS id,
  il.product_id,
  il.date,
  il.invoice_date,
  sum(il.sale_qty)       AS sale_qty,
  sum(il.sale_subtotal / COALESCE(cr.rate,
                                         1.0))                                                      AS sale_subtotal,
  il.property_account_income_id,
  il.sale_invoice_id,
  il.property_account_receivable_id,
  il.customer_id,
  il.user_id,
  il.team_id,
  il.company_id,
  il.sale_state,
  il.purchase_state,
  sum(
      il.purchase_qty)                                                                              AS purchase_qty,
  sum(il.purchase_subtotal / COALESCE(cr.rate,
                                             1.0))                                                  AS purchase_subtotal,
  sum(COALESCE(il.sale_subtotal, 0.0) / COALESCE(cr.rate, 1.0)) - sum(COALESCE(il.purchase_subtotal, 0.0) / COALESCE(cr.rate, 1.0)) AS marge_subtotal,
  il.property_account_expense_id,
  il.purchase_invoice_id,
  il.property_payable_id,
  il.supplier_id,
  t.categ_id                                                                                        AS categ_id
                """ % self.env['res.currency']._select_companies_rates()
        return select_str

    def _from(self):
        from_str = """
(SELECT
  LEAST(out_invoice.id, in_invoice.id)                     AS id,
  LEAST(out_invoice.product_id, in_invoice.product_id)     AS product_id,
  LEAST(out_invoice.invoice_date, in_invoice.invoice_date) AS invoice_date,
  LEAST(out_invoice.create_date, in_invoice.create_date) AS date,
  out_invoice.quantity                                     AS sale_qty,
  out_invoice.price_subtotal                               AS sale_subtotal,
  out_invoice.account_id                                   AS property_account_income_id,
  out_invoice.move_id                                   AS sale_invoice_id,
  out_invoice.invoice_account_id                           AS property_account_receivable_id,
  out_invoice.partner_id                                   AS customer_id,
  CASE WHEN out_invoice.user_id NOTNULL
    THEN out_invoice.user_id
  ELSE in_invoice.user_id END                              AS user_id,
  CASE WHEN out_invoice.team_id NOTNULL
    THEN out_invoice.team_id
  ELSE in_invoice.team_id END                              AS team_id,
  CASE WHEN out_invoice.company_id NOTNULL
    THEN out_invoice.company_id
  ELSE in_invoice.company_id END                           AS company_id,
  CASE WHEN out_invoice.currency_id NOTNULL
    THEN out_invoice.currency_id
  ELSE in_invoice.currency_id END                           AS currency_id,
  out_invoice.state                                        AS sale_state,
  in_invoice.state                                         AS purchase_state,
  in_invoice.quantity                                     AS purchase_qty,
  in_invoice.price_subtotal                               AS purchase_subtotal,
  in_invoice.account_id                                   AS property_account_expense_id,
  in_invoice.move_id                                   AS purchase_invoice_id,
  in_invoice.invoice_account_id                           AS property_payable_id,
  in_invoice.partner_id                                   AS supplier_id

FROM (SELECT
        ail.id,
        ail.product_id,
        CASE WHEN ai.type = 'out_refund'
           THEN ail.quantity * -1
         ELSE ail.quantity END                              AS quantity,
        ail.product_uom_id,
        ail.price_subtotal,
        ail.account_id,
        ai.id         AS move_id,
        ai.invoice_date,
        ai.create_date,
        ail.account_id AS invoice_account_id,
        ai.partner_id,
        CASE WHEN so.user_id NOTNULL
            THEN so.user_id
        ELSE ai.invoice_user_id END                              AS user_id,
        ai.team_id,
        ai.state,
        ai.company_id,
        ai.currency_id,
        so.id         AS so_id,
        so.name       AS so_name,
        so.date_order AS so_date_order
      FROM account_move_line AS ail
        JOIN account_move ai
          ON ail.move_id = ai.id AND ai.type IN ('out_invoice', 'out_refund') AND ai.state NOT IN ('cancel')
        LEFT JOIN sale_order AS so ON ai.invoice_origin = so.name AND ai.type = 'out_invoice') AS out_invoice

  FULL OUTER JOIN
  (SELECT
     ail.id,
     ail.product_id,
     ail.product_uom_id,
     CASE WHEN ai.type = 'in_refund'
       THEN ail.quantity * -1
     ELSE ail.quantity END                              AS quantity,
     ail.price_subtotal,
     ail.account_id,
     ai.id         AS move_id,
     ai.invoice_date,
     ai.create_date,
     ail.account_id AS invoice_account_id,
     ai.partner_id,
     CASE WHEN po.create_uid NOTNULL
        THEN po.create_uid
        ELSE ai.invoice_user_id END                              AS user_id,
     ai.team_id,
     ai.state,
     ai.company_id,
     ai.currency_id,
     po.id         AS po_id,
     po.name       AS po_name,
     po.date_order AS po_date_order,
     po.origin     AS po_origin
   FROM account_move_line AS ail
     JOIN account_move ai
       ON ail.move_id = ai.id AND ai.type IN ('in_invoice', 'in_refund') AND ai.state NOT IN ('cancel')
     LEFT JOIN purchase_order_line AS pol ON ail.purchase_line_id = pol.id
     LEFT JOIN purchase_order AS po ON pol.order_id = po.id ) AS in_invoice
    ON out_invoice.so_name = in_invoice.po_origin AND in_invoice.product_id = out_invoice.product_id
    ) AS il
  LEFT JOIN product_product p ON (il.product_id = p.id)
  LEFT JOIN product_template t ON (p.product_tmpl_id = t.id)
  LEFT JOIN currency_rate cr ON (cr.currency_id = il.currency_id AND
                                 cr.company_id = il.company_id AND
                                 cr.date_start <= COALESCE(il.date, now()) AND
                                 (cr.date_end IS NULL OR cr.date_end > COALESCE(il.date, now())))
        """
        return from_str

    def _group_by(self):
        group_by_str = """
            GROUP BY
             il.date,
             il.invoice_date,
             il.product_id,
             il.user_id,
             il.team_id,
             il.company_id,
             il.sale_invoice_id,
             il.purchase_invoice_id,
             il.sale_state,
             il.purchase_state,
             il.property_payable_id,
             il.property_account_receivable_id,
             il.property_account_income_id,
             il.property_account_expense_id,
             il.customer_id,
             il.supplier_id,
             t.categ_id

        """
        return group_by_str


    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        query = """CREATE or REPLACE VIEW %s as (
    %s
    FROM (%s)
    %s
    )""" % (self._table, self._select(), self._from(), self._group_by())
        self.env.cr.execute(query)
