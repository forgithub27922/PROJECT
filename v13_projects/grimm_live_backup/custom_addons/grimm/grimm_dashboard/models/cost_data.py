from odoo import models, fields, api, _
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)


class CostData(models.Model):
    _name = 'grimm.cost.data'
    _description = 'Grimm Cost Data'

    team_id = fields.Many2one('crm.team', 'Sales Channel', readonly=True)
    amount_total_ct = fields.Float(string='Total Amount Current Quarter', readonly=True)
    amount_total_prev = fields.Float(string='Total Amount Previous Quarter', readonly=True)
    percentage = fields.Float(string='Percentage', digits=(16, 2), readonly=True)
    type = fields.Char('Type', readonly=True)

    def disp_stats(self):
        _logger.info('[Cost Data CRON JOB] Creating statistical data on Sales')
        dt = datetime.now()
        prev_qrt = self.check_quarter(dt, 'prev')
        prev_quarter_start_date = '%s-%s-01 00:00:00' % (prev_qrt[0], prev_qrt[1])
        ct_qrt = self.check_quarter(dt, 'ct')
        ct_qtr_start_date = '%s-%s-01 00:00:00' % (ct_qrt[0], ct_qrt[1])

        SaleOrderQtr = self.env['sale.order'].search([('create_date', '>=', prev_quarter_start_date)])
        SaleOrderPrevQtr = SaleOrderQtr.search(
            [('create_date', '>=', prev_quarter_start_date), ('create_date', '<', ct_qtr_start_date)])
        SaleOrderCtQtr = SaleOrderQtr.search([('create_date', '>=', ct_qtr_start_date)])

        prev_mon = (str(int(dt.strftime('%Y')) - 1), '12') if int(dt.strftime('%m')) == 1 else \
            (dt.strftime('%Y'), str(int(dt.strftime('%m')) - 1))
        prev_mon_start_date = '%s-%s-01 00:00:00' % (prev_mon[0], prev_mon[1])
        ct_mon = (dt.strftime('%Y'), dt.strftime('%m'))
        ct_mon_start_date = '%s-%s-01 00:00:00' % (ct_mon[0], ct_mon[1])
        print('DATE', prev_mon_start_date, ct_mon_start_date)
        SaleOrderMon = self.env['sale.order'].search([('create_date', '>=', prev_mon_start_date)])
        SaleOrderPrevMon = SaleOrderMon.search(
            [('create_date', '>=', prev_mon_start_date), ('create_date', '<', ct_mon_start_date)])
        SaleOrderCtMon = SaleOrderMon.search([('create_date', '>=', ct_mon_start_date)])

        service_pqtr = SaleOrderPrevQtr.filtered(lambda rec: rec.team_id.id == 3).mapped('amount_total')
        service_cqtr = SaleOrderCtQtr.filtered(lambda rec: rec.team_id.id == 3).mapped('amount_total')
        sales_pqtr = SaleOrderPrevQtr.filtered(lambda rec: rec.team_id.id == 1).mapped('amount_total')
        sales_cqtr = SaleOrderCtQtr.filtered(lambda rec: rec.team_id.id == 1).mapped('amount_total')
        shop_pqtr = SaleOrderPrevQtr.filtered(lambda rec: rec.team_id.id == 2).mapped('amount_total')
        shop_cqtr = SaleOrderCtQtr.filtered(lambda rec: rec.team_id.id == 2).mapped('amount_total')
        project_pqtr = SaleOrderPrevQtr.filtered(lambda rec: rec.team_id.id == 8).mapped('amount_total')
        project_cqtr = SaleOrderCtQtr.filtered(lambda rec: rec.team_id.id == 8).mapped('amount_total')

        service_pmon = SaleOrderPrevMon.filtered(lambda rec: rec.team_id.id == 3).mapped('amount_total')
        service_cmon = SaleOrderCtMon.filtered(lambda rec: rec.team_id.id == 3).mapped('amount_total')
        sales_pmon = SaleOrderPrevMon.filtered(lambda rec: rec.team_id.id == 1).mapped('amount_total')
        sales_cmon = SaleOrderCtMon.filtered(lambda rec: rec.team_id.id == 1).mapped('amount_total')
        shop_pmon = SaleOrderPrevMon.filtered(lambda rec: rec.team_id.id == 2).mapped('amount_total')
        shop_cmon = SaleOrderCtMon.filtered(lambda rec: rec.team_id.id == 2).mapped('amount_total')
        project_pmon = SaleOrderPrevMon.filtered(lambda rec: rec.team_id.id == 8).mapped('amount_total')
        project_cmon = SaleOrderCtMon.filtered(lambda rec: rec.team_id.id == 8).mapped('amount_total')

        amt_service_prev_qtr, amt_service_ct_qtr = round(sum(service_pqtr), 2), round(sum(service_cqtr), 2)
        amt_service_prev_mon, amt_service_ct_mon = round(sum(service_pmon), 2), round(sum(service_cmon), 2)
        try:
            per_service_qtr = (amt_service_ct_qtr - amt_service_prev_qtr) / amt_service_ct_qtr if \
                amt_service_prev_qtr < amt_service_ct_qtr else (amt_service_prev_qtr - amt_service_ct_qtr) / amt_service_prev_qtr
            per_service_mon = (amt_service_ct_mon - amt_service_prev_mon) / amt_service_ct_mon if \
                amt_service_prev_mon < amt_service_ct_mon else (amt_service_prev_mon - amt_service_ct_mon) / amt_service_prev_mon
        except ZeroDivisionError:
            per_service_qtr, per_service_mon = 0, 0
        amt_sales_prev_qtr, amt_sales_ct_qtr = round(sum(sales_pqtr), 2), round(sum(sales_cqtr), 2)
        amt_sales_prev_mon, amt_sales_ct_mon = round(sum(sales_pmon), 2), round(sum(sales_cmon), 2)
        try:
            per_sales_qtr = (amt_sales_ct_qtr - amt_sales_prev_qtr) / amt_sales_ct_qtr if \
                amt_sales_prev_qtr < amt_sales_ct_qtr else (amt_sales_prev_qtr - amt_sales_ct_qtr) / amt_sales_prev_qtr
            per_sales_mon = (amt_sales_ct_mon - amt_sales_prev_mon) / amt_sales_ct_mon if \
                amt_sales_prev_mon < amt_sales_ct_mon else (amt_sales_prev_mon - amt_sales_ct_mon) / amt_sales_prev_mon
        except ZeroDivisionError:
            per_sales_qtr, per_sales_mon = 0, 0
        amt_shop_prev_qtr, amt_shop_ct_qtr = round(sum(shop_pqtr), 2), round(sum(shop_cqtr), 2)
        amt_shop_prev_mon, amt_shop_ct_mon = round(sum(shop_pmon), 2), round(sum(shop_cmon), 2)
        try:
            per_shop_qtr = (amt_shop_ct_qtr - amt_shop_prev_qtr) / amt_shop_ct_qtr if \
                amt_shop_prev_qtr < amt_shop_ct_qtr else (amt_shop_prev_qtr - amt_shop_ct_qtr) / amt_shop_prev_qtr
            per_shop_mon = (amt_shop_ct_mon - amt_shop_prev_mon) / amt_shop_ct_mon if \
                amt_shop_prev_mon < amt_shop_ct_mon else (amt_shop_prev_mon - amt_shop_ct_mon) / amt_shop_prev_mon
        except ZeroDivisionError:
            per_shop_qtr, per_shop_mon = 0, 0
        amt_project_prev_qtr, amt_project_ct_qtr = round(sum(project_pqtr), 2), round(sum(project_cqtr), 2)
        amt_project_prev_mon, amt_project_ct_mon = round(sum(project_pmon), 2), round(sum(project_cmon), 2)
        try:
            per_project_qtr = (amt_project_ct_qtr - amt_project_prev_qtr) / amt_project_ct_qtr if \
                amt_project_prev_qtr < amt_project_ct_qtr else (amt_project_prev_qtr - amt_project_ct_qtr) / amt_project_prev_qtr
            per_project_mon = (amt_project_ct_mon - amt_project_prev_mon) / amt_project_ct_mon if \
                amt_project_prev_mon < amt_project_ct_mon else (amt_project_prev_mon - amt_project_ct_mon) / amt_project_prev_mon
        except ZeroDivisionError:
            per_project_qtr, per_project_mon = 0, 0

        print(amt_service_prev_qtr, amt_service_ct_qtr, per_service_qtr)
        print(amt_sales_prev_qtr, amt_sales_ct_qtr, per_sales_qtr)
        print(amt_shop_prev_qtr, amt_shop_ct_qtr, per_shop_qtr)
        print(amt_project_prev_qtr, amt_project_ct_qtr, per_project_qtr)

        self.create({'team_id': 3, 'amount_total_ct': amt_service_ct_qtr, 'amount_total_prev': amt_service_prev_qtr,
                     'percentage': per_service_qtr * 100, 'type': 'quarterly'})
        self.create({'team_id': 1, 'amount_total_ct': amt_sales_ct_qtr, 'amount_total_prev': amt_sales_prev_qtr,
                     'percentage': per_sales_qtr * 100, 'type': 'quarterly'})
        self.create({'team_id': 2, 'amount_total_ct': amt_shop_ct_qtr, 'amount_total_prev': amt_shop_prev_qtr,
                     'percentage': per_shop_qtr * 100, 'type': 'quarterly'})
        self.create({'team_id': 8, 'amount_total_ct': amt_project_ct_qtr, 'amount_total_prev': amt_project_prev_qtr,
                     'percentage': per_project_qtr * 100, 'type': 'quarterly'})

        self.create(
            {'team_id': 3, 'amount_total_ct': amt_service_ct_mon, 'amount_total_prev': amt_service_prev_mon,
             'percentage': per_service_mon * 100, 'type': 'monthly'})
        self.create({'team_id': 1, 'amount_total_ct': amt_sales_ct_mon, 'amount_total_prev': amt_sales_prev_mon,
                     'percentage': per_sales_mon * 100, 'type': 'monthly'})
        self.create({'team_id': 2, 'amount_total_ct': amt_shop_ct_mon, 'amount_total_prev': amt_shop_prev_mon,
                     'percentage': per_shop_mon * 100, 'type': 'monthly'})
        self.create(
            {'team_id': 8, 'amount_total_ct': amt_project_ct_mon, 'amount_total_prev': amt_project_prev_mon,
             'percentage': per_project_mon * 100, 'type': 'monthly'})

    def check_quarter(self, dt, qtr):
        if int(dt.strftime('%m')) in list(range(1, 4)):
            if qtr == 'ct':
                return (dt.strftime('%Y'), '01')
            elif qtr == 'prev':
                return (str(int(dt.strftime('%Y')) - 1), '09')
        elif int(dt.strftime('%m')) in list(range(4, 7)):
            if qtr == 'ct':
                return (dt.strftime('%Y'), '04')
            elif qtr == 'prev':
                return (dt.strftime('%Y'), '01')
        elif int(dt.strftime('%m')) in list(range(7, 10)):
            if qtr == 'ct':
                return (dt.strftime('%Y'), '07')
            elif qtr == 'prev':
                return (dt.strftime('%Y'), '04')
        elif int(dt.strftime('%m')) in list(range(10, 13)):
            if qtr == 'ct':
                return (dt.strftime('%Y'), '10')
            elif qtr == 'prev':
                return (dt.strftime('%Y'), '07')
