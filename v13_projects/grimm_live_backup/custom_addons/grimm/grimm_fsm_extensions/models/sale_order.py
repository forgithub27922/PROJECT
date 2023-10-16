#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
#  config.py
#
#  Copyright 2015 Grimm Gastrobedarf
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
from datetime import datetime, timedelta
import logging


_logger = logging.getLogger(__name__)

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    timer_start = fields.Datetime('Timer Start')
    timer_stop = fields.Datetime('Timer Stop')

class ProjectTaskCreateTimesheet(models.TransientModel):
    _inherit = 'project.task.create.timesheet'

    def save_timesheet(self):
        current_date_time = fields.datetime.now()
        values = {
            'task_id': self.task_id.id,
            'project_id': self.task_id.project_id.id,
            'date': fields.Date.context_today(self),
            'name': self.description,
            'user_id': self.env.uid,
            'unit_amount': self.time_spent,
            'timer_start': self.task_id.timesheet_timer_start,
            'timer_stop': current_date_time,
        }
        self.task_id.write({
            'timesheet_timer_start': False,
            'timesheet_timer_pause': False,
            'timesheet_timer_last_stop': current_date_time,
        })
        return self.env['account.analytic.line'].create(values)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    free_products = fields.One2many('project.task.product', 'order_id', 'Free Text Product')
    display_prod_in_ticket = fields.Boolean("Produktinformationen im Ticket anzeigen", default=False)

    def action_view_task(self):
        self.ensure_one()
        action = super(SaleOrder, self).action_view_task()
        form_view_id = self.env.ref('grimm_fsm_extensions.grimm_fsm_project_task_form_view').id
        if len(self.tasks_ids) == 1:
            action['views'] = [(form_view_id, 'form')]
        return action

    def write(self, vals):
        '''
        :param vals:
        :return:
        '''
        result = super(SaleOrder, self).write(vals)
        for this in self:
            product_sku = this.order_line.mapped('product_id.default_code')
            fsm_product = this.with_context(force_company=1).order_line.mapped('product_id.project_id.is_fsm')
            #if any(fsm_product) and 'AZTIME' in product_sku and 'GRIMM-KLM001' not in product_sku:
            if any(fsm_product) and 'GRIMM-KLM001' not in product_sku:
                product_id = self.env['product.product'].search([('default_code','=', 'GRIMM-KLM001')],limit=1)
                if product_id:
                    new_line = self.env['sale.order.line'].create({'order_id':this.id,'product_id':product_id.id,"route_id":False,'product_uom_qty':1})
            related_tasks = self.env['project.task'].search([('sale_order_id', '=', this.id)])
            for task in related_tasks:
                for asset in this.asset_ids:
                    asset.task_id = task.id

        return result

    @api.model
    def create(self, vals):
        '''
        Inherited for task OD-1271 (Changing name of product variant, changes name of prodcut.template)
        :param vals:
        :return:
        '''
        new_order_id = super(SaleOrder, self).create(vals)
        product_sku = new_order_id.order_line.mapped('product_id.default_code')
        fsm_product = new_order_id.with_context(force_company=1).order_line.mapped('product_id.project_id.is_fsm')
        #if any(fsm_product) and 'AZTIME' in product_sku and 'GRIMM-KLM001' not in product_sku:
        if any(fsm_product) and 'GRIMM-KLM001' not in product_sku:
            product_id = self.env['product.product'].search([('default_code', '=', 'GRIMM-KLM001')], limit=1)
            if product_id:
                new_line = self.env['sale.order.line'].create({'order_id': new_order_id.id,"route_id":False, 'product_id': product_id.id, 'product_uom_qty': 1})
        return new_order_id

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _timesheet_create_task_prepare_values(self, project):
        res = super(SaleOrderLine, self)._timesheet_create_task_prepare_values(project)
        if self.order_id.contact:
            res["claim_contact"] = self.order_id.contact.id
        return res

    def _check_line_unlink(self):
        """
        Check wether a line can be deleted or not.

        Lines cannot be deleted if the order is confirmed; downpayment
        lines who have not yet been invoiced bypass that exception.
        :rtype: recordset sale.order.line
        :returns: set of lines that cannot be deleted

        GRIMM - Inherited for allow remove SPA001 article.
        """
        grimm_spa_product = self.env['product.product'].search([('default_code', '=', 'GRIMM-SPA001')],)
        if grimm_spa_product:
            return self.filtered(lambda line: (line.product_id.id == grimm_spa_product.id and line.invoice_lines) or (line.product_id.id != grimm_spa_product.id and line.state in ('sale', 'done') and (line.invoice_lines or not line.is_downpayment)))
        else:
            return self.filtered(lambda line: line.state in ('sale', 'done') and (line.invoice_lines or not line.is_downpayment))