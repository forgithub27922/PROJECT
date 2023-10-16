# -*- coding: utf-8 -*-

import datetime
from odoo import fields, models, tools, api, _
from functools import lru_cache


class ReportResumenXlsx(models.AbstractModel):
    _name = "report.report_xlsx.resumen_xlsx"
    _inherit = "report.report_xlsx.abstract"
    _description = "Reporte Resumen Inventarios"

    def generate_xlsx_report(self, workbook, data, records):
        columns = [
            ('A:A', 10),        # A
            ('B:B', 10),        # A
            ('C:C', 30),        # B
            ('C:P', 15),        # C
        ]
        formats = [
            'string_left',              # A
            'string_left',              # B
            'string_right_border',      # C
            
            'money_format',             # D
            'integer_format',           # E
            'money_right_format',       # F

            'money_format',             # G
            'integer_format',           # H
            'money_right_format',       # I            
            
            'money_format',             # J
            'integer_format',           # K
            'money_right_format',       # L

            'money_format',             # M
            'integer_format',           # N
            'money_right_format',       # O

            'money_format',             # P
            'integer_format',           # Q
            'money_right_format',       # R

            'money_format',     # S
            'money_format',     # T
            'money_format',     # G
            'money_format',     # G
            'money_format',     # G
        ]     
        headers = [u'Código', 'Categoria', 'Producto', 'Importe', 'Cantidad', 'P.U', 'Importe', 'Cantidad', 'P.U', 'Importe', 'Cantidad', 'P.U.', 'Importe', 'Cantidad', 'P.U', '% S Ventas']
        freeze_panes = True
        for rec in records:
            datasList = rec.action_report_datas()
            for data in datasList:
                worksheet = workbook.add_worksheet(data)
                # worksheet.hide_gridlines(2)
                workbook_format = {
                    'header_format': workbook.add_format({'font_name':'Calibri', 'font_size':12, 'bold':1, 'italic':0, 'align':'center', 'valign':'vcenter', 'fg_color':'#AAAAAA', 'color':'#000000', 'bottom': 2, 'bottom_color':'#000000', 'top': 2, 'top_color':'#000000', 'left': 2, 'left_color': '#000000', 'right': 2, 'right_color': '#000000' }),
                    'string_left': workbook.add_format({'font_name':'Calibri', 'font_size':10, 'align':'left', 'valign':'vcenter', 'fg_color':'white', }),
                    'money_format': workbook.add_format({'font_name':'Calibri', 'font_size':10, 'align':'right', 'valign':'vcenter', 'num_format':'$#,##0.00;[RED]-$#,##0.00', 'fg_color':'white'}),
                    'integer_format': workbook.add_format({'font_name':'Calibri', 'font_size':10, 'align':'right', 'valign':'vcenter', 'num_format':'#,##0.00;[RED]-#,##0.00', 'fg_color':'white'}),
                    'string_right_border': workbook.add_format({'font_name':'Calibri', 'font_size':10, 'align':'left', 'valign':'vcenter', 'fg_color':'white', 'right': 2, 'right_color':'#151515' }),
                    'money_right_format': workbook.add_format({'font_name':'Calibri', 'font_size':10, 'align':'right', 'valign':'vcenter', 'num_format':'$#,##0.00;[RED]-$#,##0.00', 'fg_color':'white', 'right': 2, 'right_color':'#151515'}),
                    'title_company': workbook.add_format({'font_name':'Arial', 'font_size':18, 'bold':1, 'align':'center', 'valign':'vcenter', 'color':'#032C46'}),
                    'string_center': workbook.add_format({'font_name':'Calibri', 'font_size':10, 'align':'center', 'valign':'vcenter', 'fg_color':'white', 'bottom': 4, 'bottom_color':'#D9D9D9'}),

                    'string_rigth': workbook.add_format({'font_name':'Calibri', 'font_size':10, 'align':'right', 'valign':'vcenter', 'fg_color':'white', 'bottom': 4, 'bottom_color':'#D9D9D9'}),
                    'string_center_bold': workbook.add_format({'font_name':'Calibri', 'font_size':10, 'bold':1, 'align':'center', 'valign':'vcenter', 'fg_color':'white', 'bottom': 4, 'bottom_color':'#D9D9D9'}),
                    'string_left_bold': workbook.add_format({'font_name':'Calibri', 'font_size':10, 'bold':1, 'align':'left', 'valign':'vcenter', 'fg_color':'white', 'bottom': 4, 'bottom_color':'#D9D9D9'}),
                    'string_rigth_bold': workbook.add_format({'font_name':'Calibri', 'font_size':10, 'bold':1, 'align':'right', 'valign':'vcenter', 'fg_color':'white', 'bottom': 4, 'bottom_color':'#D9D9D9'}),
                    'percent': workbook.add_format({ 'font_name':'Calibri', 'font_size':10, 'align':'right', 'valign':'vcenter', 'num_format':'0.00%', 'fg_color':'white', 'bottom':4, 'bottom_color':'#D9D9D9' }),
                    'percent_left': workbook.add_format({ 'font_name':'Calibri', 'font_size':10, 'align':'right', 'valign':'vcenter', 'num_format':'0.00%', 'fg_color':'white', 'bottom':4, 'bottom_color':'#D9D9D9' }),
                    'percent_right': workbook.add_format({ 'font_name':'Calibri', 'font_size':10, 'align':'right', 'valign':'vcenter', 'num_format':'0.00%', 'fg_color':'white', 'bottom':4, 'bottom_color':'#D9D9D9'}),
                    
                    
                    'datetime': workbook.add_format({ 'font_name':'Calibri', 'font_size':10, 'align':'right', 'valign':'vcenter', 'num_format':'yyyy-mm-dd hh:mm:ss', 'fg_color':'white', 'bottom': 4, 'bottom_color':'#D9D9D9' }),
                    'date': workbook.add_format({ 'font_name':'Calibri', 'font_size':10, 'align':'center', 'valign':'vcenter', 'num_format':'yyyy-mm-dd', 'fg_color':'white', 'bottom': 4, 'bottom_color':'#D9D9D9' }),
                }
                for column in columns:
                    if len(column) == 2:
                        worksheet.set_column(column[0], column[1])

                worksheet.merge_range('D1:F1', 'Inventario Inicial', workbook_format['header_format'])
                worksheet.merge_range('G1:I1', 'Compras', workbook_format['header_format'])
                worksheet.merge_range('J1:L1', 'Salidas', workbook_format['header_format'])
                worksheet.merge_range('M1:O1', 'Inventario Final', workbook_format['header_format'])
                worksheet.merge_range('P1R1', 'Costo de Ventas', workbook_format['header_format'])

                row = 2
                datas = datasList.get(data)
                datas.insert(0, headers)
                if len(datas):
                    if freeze_panes:
                        worksheet.freeze_panes(row, 3)
                    header = datas[0]
                    body = datas[1:]
                    worksheet.write_row('A%s'%(row), header, workbook_format.get('header_format'))
                    row += 1
                    datas_list = []
                    for i, d in enumerate(body):
                        datas_list.append(list(d))
                    datas_list = zip(*datas_list)
                    for i, d in enumerate(datas_list):
                        try:
                            formato = workbook_format.get(formats[i], 'string_left')
                        except:
                            formato = workbook_format.get('string_left')
                        worksheet.write_column(row-1, i, d, formato)


        # sheet = workbook.add_worksheet("Report")
        # for i, obj in enumerate(partners):
        #     bold = workbook.add_format({"bold": True})
        #     sheet.write(i, 0, obj.name, bold)


class bfiskur_wiz(models.TransientModel):
    _name = "report.resumen.inventarios.wiz"
    _description = 'Resumen Inventarios Wizard'

    # 

    name = fields.Char(string='Name', default="")
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, default=lambda self: self.env.company)
    warehouse_ids = fields.Many2many('stock.warehouse', required=True)
    date_start = fields.Date(string='Date Start', required=True, default=datetime.datetime.now().strftime('%Y-%m-01'))
    date_end = fields.Date(string='Date End', required=True, default=fields.Date.context_today)

    def action_report(self):
        a = str(self.date_start).replace('-', '')
        b = str(self.date_end).replace('-', '')
        self.name = 'Resumen de Inventarios %s - %s'%(a, b)
        res =  self.env.ref('resumeninv_yeidala.report_xlsx_resumenwiz').report_action(self, config=False)
        return res

    def getinv_datas(self, product_id, dateinv, loc_id):
        qval = """
SELECT SUM(COALESCE("valuation".quantity, 0)) AS "quantity", SUM(COALESCE("valuation".value, 0)) AS "value"
FROM(
    SELECT
        SUM(COALESCE(svl.quantity, 0)) AS "quantity",
        SUM(COALESCE(svl.value, 0)) AS "value"
    FROM stock_valuation_layer svl
    LEFT JOIN stock_move sm ON (svl.stock_move_id = sm.id)
    WHERE 
        svl.product_id = {p_id} AND
        ((svl.create_date at time zone 'utc' at time zone 'America/Mexico_City')::timestamp) < '{datestart} 00:00:00' AND
        sm.location_dest_id = {loc_id} 
    GROUP BY svl.product_id
    UNION ALL
    SELECT 
        SUM(COALESCE(svl.quantity, 0)) AS "quantity",
        SUM(COALESCE(svl.value, 0)) AS "value"
    FROM stock_valuation_layer svl
    LEFT JOIN stock_move sm ON (svl.stock_move_id = sm.id)
    WHERE 
        svl.product_id = {p_id} AND
        ((svl.create_date at time zone 'utc' at time zone 'America/Mexico_City')::timestamp) < '{datestart} 00:00:00' AND
        sm.location_id = {loc_id} 
    GROUP BY svl.product_id
) AS "valuation";
        """.format(p_id=product_id, datestart='%s'%(dateinv), loc_id=loc_id)
        self._cr.execute(qval)
        imp, qty, pu = 0.0, 0.0, 0.0
        for val in self._cr.dictfetchall():
            quantity = val.get('quantity', 0.0) or 0.0
            value = val.get('value', 0.0) or 0.0
            qty += quantity
            imp += value
            pu += 0 if quantity == 0 else (value / quantity)
        return (imp, qty, pu)

    def getcompras_datas(self, product_id, datestart, datestop, loc_id):
        qval = """
SELECT
    SUM(COALESCE(svl.quantity, 0)) AS "quantity",
    SUM(COALESCE(svl.value, 0)) AS "value"
FROM stock_valuation_layer svl
LEFT JOIN stock_move sm ON (svl.stock_move_id = sm.id)
LEFT JOIN stock_location sl ON (sm.location_id = sl.id)
WHERE 
    svl.product_id = {p_id} AND
    ((svl.create_date at time zone 'utc' at time zone 'America/Mexico_City')::timestamp) >= '{datestart} 00:00:00' AND
    ((svl.create_date at time zone 'utc' at time zone 'America/Mexico_City')::timestamp) <= '{datestop} 00:00:00' AND
    sl.usage = 'supplier' AND
    sm.location_dest_id = {loc_id} 
GROUP BY svl.product_id;
        """.format(p_id=product_id, datestart='%s'%(datestart), datestop='%s'%(datestop), loc_id=loc_id)
        self._cr.execute(qval)
        imp, qty, pu = 0.0, 0.0, 0.0
        for val in self._cr.dictfetchall():
            qty += val.get('quantity')
            imp += val.get('value')
            pu += val.get('value') /  val.get('quantity')
        return (imp, qty, pu)

    def getsalidas_datas(self, product_id, datestart, datestop, loc_id):
        qval = """
SELECT
    SUM(COALESCE(svl.quantity, 0)) AS "quantity",
    SUM(COALESCE(svl.value, 0)) AS "value"
FROM stock_valuation_layer svl
LEFT JOIN stock_move sm ON (svl.stock_move_id = sm.id)
LEFT JOIN stock_location sl ON (sm.location_id = sl.id)
WHERE 
    svl.product_id = {p_id} AND
    ((svl.create_date at time zone 'utc' at time zone 'America/Mexico_City')::timestamp) >= '{datestart} 00:00:00' AND
    ((svl.create_date at time zone 'utc' at time zone 'America/Mexico_City')::timestamp) <= '{datestop} 00:00:00' AND
    sl.usage = 'internal' AND
    sm.location_id = {loc_id} 
GROUP BY svl.product_id;
        """.format(p_id=product_id, datestart='%s'%(datestart), datestop='%s'%(datestop), loc_id=loc_id)
        self._cr.execute(qval)
        imp, qty, pu = 0.0, 0.0, 0.0
        for val in self._cr.dictfetchall():
            q = abs(val.get('quantity', 0.0))
            v = abs(val.get('value', 0.0))
            qty += q
            imp += v
            pu += 0 if q == 0 else (v/q)
        return (imp, qty, pu)        


    def action_report_datas(self):
        reportDatas = {}
        ProductProduct = self.env['product.product']
        StockValuation = self.env['stock.valuation.layer']
        for ws_id in self.warehouse_ids:
            if not ws_id.account_analytic_id:
                continue
            if ws_id.id not in reportDatas:
                reportDatas[ ws_id.name ] = []
            qprod = """
                SELECT
                    DISTINCT svl.product_id
                FROM stock_valuation_layer svl
                WHERE
                    svl.product_id IS NOT NULL AND 
                    ((svl.create_date at time zone 'utc' at time zone 'America/Mexico_City')::timestamp) >= '%s' AND 
                    ((svl.create_date at time zone 'utc' at time zone 'America/Mexico_City')::timestamp) <= '%s'
                GROUP BY svl.product_id
            """%(self.date_start, self.date_end)
            self._cr.execute(qprod)
            p_ids = self._cr.fetchall()
            for p_id in p_ids:
                """
                val_ids = StockValuation.read_group(
                    ["&","&",("product_id","=",p_id[0]),("stock_move_id.location_dest_id","=",ws_id.lot_stock_id.id),('create_date','<=',self.date_start)], 
                    ['quantity', 'value'], ['create_date'], offset=0, limit=1, orderby='create_date DESC ')
                for val_id in val_ids:
                    print('---- val_id', val_id)
                """
                new_date = self.date_end + datetime.timedelta(days=1)
                ini_vals = self.getinv_datas( p_id[0], self.date_start, ws_id.lot_stock_id.id )
                fin_vals = self.getinv_datas( p_id[0], new_date, ws_id.lot_stock_id.id )
                comp_vals = self.getcompras_datas(p_id[0], self.date_start, self.date_end, ws_id.lot_stock_id.id)
                salidas_vals = self.getsalidas_datas(p_id[0], self.date_start, self.date_end, ws_id.lot_stock_id.id)

                product_id = ProductProduct.browse(p_id[0])
                datasTmp = [
                    '%s'%( product_id.default_code ),
                    '%s'%( product_id.categ_id.display_name ),
                    '%s'%( product_id.name ),

                    # Inicial
                    ini_vals[0],
                    ini_vals[1],
                    ini_vals[2],
                    # Compras
                    comp_vals[0],
                    comp_vals[1],
                    comp_vals[2],
                    # Salidas
                    salidas_vals[0],
                    salidas_vals[1],
                    salidas_vals[2],                    
                    # Final
                    fin_vals[0],
                    fin_vals[1],
                    fin_vals[2],
                    # CostoVentas
                    ini_vals[0] + comp_vals[0] - fin_vals[0],
                    ini_vals[1] + comp_vals[1] - fin_vals[1],
                    ini_vals[2] + comp_vals[2] - fin_vals[2]
                ]
                reportDatas[ws_id.name].append(datasTmp)

        return reportDatas



class StockInvoiceReport(models.Model):
    _name = "report.resumen.inventarios"
    _description = "Resumen Inventarios"
    # _auto = False
    _rec_name = 'warehouse_id'
    _order = 'warehouse_id desc'

    # ==== Warehouse fields ====
    warehouse_id = fields.Many2one('stock.warehouse', readonly=True)
    account_analytic_id = fields.Many2one('account.analytic.account', string="Analytic Account", readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    lot_stock_id = fields.Many2one('stock.location', string='Location Stock', readonly=True)

    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    product_uom_qty = fields.Float(string='Uom QTY', readonly=True)
    price_subtotal = fields.Float(string='Subtotal', readonly=True)
    price_unit = fields.Float(string='Price Unit', readonly=True)

    def sw_report(self, date_start, date_stop, company_id):
        ProductProduct = self.env['product.product']
        datas = []
        for ws_id in self.env['stock.warehouse'].sudo().search([('company_id', '=', company_id)]):
            if not ws_id:
                continue

            # Busca Productos
            qpol = """
SELECT 
    pol.product_id, 
    SUM(pol.product_uom_qty) AS "product_uom_qty",
    SUM(pol.price_subtotal) AS "price_subtotal"
FROM purchase_order_line pol
WHERE 
    pol.product_id IS NOT NULL AND 
    pol.state = 'purchase' AND 
    pol.account_analytic_id = %s AND 
    pol.date_planned >= '%s' AND 
    pol.date_planned <= '%s'
GROUP BY pol.product_id"""%(ws_id.account_analytic_id.id, date_start, date_stop)
            self._cr.execute(qpol)
            for product_id in self._cr.dictfetchall():
                p_id = ProductProduct.browse(product_id.get('product_id'))
                datasTmp = {
                    'warehouse_id': ws_id.id,
                    'account_analytic_id': ws_id.account_analytic_id.id,
                    'company_id': ws_id.company_id.id,
                    'lot_stock_id': ws_id.lot_stock_id.id,
                    'product_id': product_id.get('product_id'),
                    'product_uom_qty': product_id.get('product_uom_qty'),
                    'price_subtotal': product_id.get('price_subtotal'),
                    'price_unit': p_id.standard_price
                }
                datas.append(datasTmp)


        print('---- product_ids', datas)
        self.env.cr.execute("TRUNCATE report_inventory_summary;")

    # def init(self):
    #     r = self.sw_report('2021-11-01', '2021-11-30', 12)
