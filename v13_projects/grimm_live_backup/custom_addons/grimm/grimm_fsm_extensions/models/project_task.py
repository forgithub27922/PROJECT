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
from odoo.exceptions import ValidationError
from odoo.tools.misc import formatLang, get_lang
import requests
import urllib.parse
import logging


_logger = logging.getLogger(__name__)
class TaskProductWizard(models.TransientModel):
    _name = 'task.product.wizard'
    _description = 'Product Wizard'

    product_name = fields.Char(string="name")
    product_qty = fields.Char(string="Quantity")
    product_price = fields.Char(string="Price")
    product_number = fields.Char(string="Artikle No.")
    task_id = fields.Many2one('project.task', string="Project Task")


    def action_store(self):
        self.ensure_one()
        create_vals = {}
        create_vals["product_name"] = self.product_name
        create_vals["product_qty"] = str(self.product_qty).replace(",",".")
        #create_vals["product_price"] = str(self.product_price).replace(",",".")
        create_vals["task_id"] = self.task_id.id
        order_id = self.task_id.sale_order_id

        grimm_spa_product = self.env['product.product'].search([('default_code', '=','GRIMM-SPA001')],)
        if not grimm_spa_product:
            grimm_spa_product = self.env['product.template'].sudo().create({"name":"GRIMM Ersatzteil", "default_code":"GRIMM-SPA001","type":"service"})
            grimm_spa_product = grimm_spa_product.product_variant_id
        try:
            project_task_product = self.env["project.task.product"].create(create_vals)
            sale_order_line = self.env["sale.order.line"].create({"order_id":order_id.id,"route_id":False,"product_id":grimm_spa_product.id,"name":"%s - %s"%(project_task_product.product_name or '',project_task_product.product_number or ''),"price_unit":project_task_product.product_price or 0,"product_uom_qty":project_task_product.product_qty})
            project_task_product.order_line_id = sale_order_line.id
        except:
            raise ValidationError(_('You have defined wrong value.'))
        return True


class ProjectTaskProduct(models.Model): # After discussion with Tobias changed to regular model instead of Transient Model
    _name = 'project.task.product'
    _description = 'Project Task Product'

    product_name = fields.Char(string="Name")
    product_qty = fields.Float(string="Quantity")
    product_price = fields.Float(string="Price")
    product_number = fields.Char(string="Artikle No.")
    task_id = fields.Many2one('project.task', string="Project Task")
    order_id = fields.Many2one('sale.order', string="Order ID")
    order_line_id = fields.Many2one('sale.order.line', string="Order Line ID")

    def write(self, vals):
        result = super(ProjectTaskProduct, self).write(vals)
        for this in self:
            if this.task_id and this.task_id.sale_order_id and not this.order_id:
                this.order_id = this.task_id.sale_order_id.id
            if this.order_id and not this.task_id:
                task_id = self.env["project.task"].search([('sale_order_id', '=', this.order_id.id)])
                if task_id:
                    this.task_id = task_id.id
            if this.order_line_id:
                this.order_line_id.write({"name":"%s - %s"%(this.product_name or '',this.product_number or ''),"price_unit":this.product_price,"product_uom_qty":this.product_qty})
        return result

    def unlink(self):
        if self.order_line_id:
            self.order_line_id.unlink()
        return super(ProjectTaskProduct, self).unlink()

    @api.model
    def create(self, vals):
        '''
        Inherited for task OD-1271 (Changing name of product variant, changes name of prodcut.template)
        :param vals:
        :return:
        '''
        res_id = super(ProjectTaskProduct, self).create(vals)
        if res_id.task_id and res_id.task_id.sale_order_id and not res_id.order_id:
            res_id.order_id = res_id.task_id.sale_order_id.id
        if res_id.order_id and not res_id.task_id:
            task_id = self.env["project.task"].search([('sale_order_id', '=', res_id.order_id.id)])
            if task_id:
                res_id.task_id = task_id.id
        return res_id

class ProjectTaskParameter(models.Model): # After discussion with Tobias changed to regular model instead of Transient Model
    _name = 'project.task.parameter'
    _description = 'Project Task Parameter'

    conductor_resistance = fields.Char(string="Protective conductor resistance Ω")
    conductor_current = fields.Char(string="Protective conductor current mA")
    insulation_resistance = fields.Char(string="Insulation resistance Ω")

    touch_current = fields.Char(string="Touch current mA")

    water_conductor_resistance = fields.Char(string="Protective conductor resistance Ω")
    water_hardness = fields.Char(string="Water hardness ºdH")
    water_total_hardness = fields.Char(string="Water Total hardness ºdH")
    full_demineralisation_conductance = fields.Char(string="Full demineralisation conductance uS/cm")
    task_ids = fields.Many2many('project.task')


    def action_store(self):
        for task in self.task_ids:
            task.conductor_resistance = self.conductor_resistance
            task.conductor_current = self.conductor_current
            task.insulation_resistance = self.insulation_resistance
            task.touch_current = self.touch_current

            task.water_conductor_resistance = self.water_conductor_resistance
            task.water_hardness = self.water_hardness
            task.water_total_hardness = self.water_total_hardness
            task.full_demineralisation_conductance = self.full_demineralisation_conductance

            if task.sale_order_id:
                product_sku = task.sale_order_id.order_line.mapped('product_id.default_code')
                if 'GRIMM-VDE001' not in product_sku:
                    product_id = self.env['product.product'].search([('default_code', '=', 'GRIMM-VDE001')], limit=1)
                    if product_id:
                        new_line = self.env['sale.order.line'].create({'order_id': task.sale_order_id.id, 'product_id': product_id.id, 'product_uom_qty': 1})
        return True

class ResUsers(models.Model):
    """ Project Task Inherited to add desired fields. """
    _inherit = "res.users"
    field_service_signature = fields.Binary(string='Field Service Signature', attachment=True)

    @api.model
    def _register_hook(self):
        super()._register_hook()
        self.SELF_WRITEABLE_FIELDS.extend(["field_service_signature"])

class ProjectProject(models.Model):
    """ Project Task Inherited to add desired fields. """
    _inherit = "project.project"
    user_ids = fields.Many2many('res.users', 'project_project_users_rel', 'project_id', 'user_id', string='Assistant manager')


class ProjectTaskCreateTimesheet(models.TransientModel):
    _inherit = 'project.task.create.timesheet'

    @api.model
    def default_get(self, fields):
        result = super(ProjectTaskCreateTimesheet, self).default_get(fields)
        result['description'] = ""
        return result

class AssetBase(models.Model):
    """ Project Task Inherited to add desired fields. """
    _inherit = "grimm.asset.asset"

    task_id = fields.Many2one('project.task', string='Task ID')

    @api.onchange('product_id')
    def onchange_product_id(self):
        result = super(AssetBase, self).onchange_product_id()
        if self.task_id and self.task_id.sale_order_id:
            self.partner_contact = self.task_id.sale_order_id.contact if self.task_id.sale_order_id.contact else self.task_id.sale_order_id.partner_id
            self.partner_invoice = self.task_id.sale_order_id.partner_invoice_id
            self.partner_delivery = self.task_id.sale_order_id.partner_shipping_id
            self.beneficiary = self.task_id.sale_order_id.beneficiary
        return result

class ProjectTask(models.Model):
    """ Project Task Inherited to add desired fields. """
    _inherit = "project.task"

    asset_id = fields.Many2one("grimm.asset.asset", string="Device")

    conductor_resistance = fields.Char(string="Protective conductor resistance Ω")
    conductor_current = fields.Char(string="Protective conductor current mA")
    insulation_resistance = fields.Char(string="Insulation resistance Ω")
    asset_lines = fields.One2many('grimm.asset.asset', 'task_id', 'Assets')

    location_ids = fields.One2many(related='asset_lines.location_ids')

    touch_current = fields.Char(string="Touch current mA")

    water_conductor_resistance = fields.Char(string="Protective conductor resistance Ω")
    water_hardness = fields.Char(string="Water hardness ºdH")
    water_total_hardness = fields.Char(string="Water Total hardness ºdH")
    full_demineralisation_conductance = fields.Char(string="Full demineralisation conductance uS/cm")
    is_parameter_done = fields.Boolean(string='Is parameter done?', compute='_get_is_parameter_done')

    free_products = fields.One2many('project.task.product', 'task_id', 'Free Text Product')

    user_ids = fields.Many2many('res.users', 'project_task_users_rel', 'task_id', 'user_id', string='Assign assistants')

    is_free_products = fields.Boolean(string='Is Free product ?', compute='_get_is_free_product')

    map_direction = fields.Html(string='Direction', compute='_compute_map_direction')

    driving_cost = fields.Selection(selection=[('ap001', 'AP001'), ('ap002', 'AP002')], string='Anfahrtspauschale')
    driving_km = fields.Float(string='Fahrkilometer')

    selected_prod_ids = fields.Many2many("product.product", string="Selected Products",compute='_compute_selected_products')
    display_offer_prod_info = fields.Boolean("Produktinformationen im Ticket anzeigen", compute="_compute_display_offer_prod_info")
    offer_prod_info = fields.Html("Produktinformationen",compute="_compute_offer_prod")

    def action_log_time(self):
        self.ensure_one()
        return self._action_create_timesheet(0)

    def _compute_display_offer_prod_info(self):
        self.display_offer_prod_info = False
        for task in self:
            if task.sale_order_id.display_prod_in_ticket:
                task.display_offer_prod_info = True

    def _compute_offer_prod(self):
        self.offer_prod_info = ""
        for task in self:
            html_info = ""
            #if task.sale_order_id.display_prod_in_ticket:
            html_info +="<table class='table table-hover'><thead><tr><tr><th>#</th><th>Name</th><th>Menge</th></tr></thead><tbody>"
            for ind,line in enumerate(task.sale_order_id.order_line):
                html_info += "<tr><td>%s</td><td>[%s]-%s</td><td>%s</td></tr>"%(ind+1, line.product_id.default_code,line.product_id.name, formatLang(self.env, line.product_uom_qty))
            html_info +="</tbody></table>"
            task.offer_prod_info = html_info


    def _compute_selected_products(self):
        for task in self:
            task.selected_prod_ids = task.sale_order_id.order_line.mapped('product_id')


    def _get_direction(self, url=False):
        if url:
            result = requests.get(url)
            return result.json()
        return False

    def display_time(self, seconds, granularity=2):
        intervals = (
            (_('weeks'), 604800),  # 60 * 60 * 24 * 7
            (_('days'), 86400),  # 60 * 60 * 24
            (_('hours'), 3600),  # 60 * 60
            (_('minutes'), 60),
            #(_('seconds'), 1),
        )
        result = []
        for name, count in intervals:
            value = seconds // count
            if value:
                seconds -= value * count
                if value == 1:
                    name = name.rstrip('s')
                result.append("{} {}".format(value, name))
        return ', '.join(result[:granularity])

    def assign_partner_latlong(self, partner, api_key):
        try:
            partner.action_validate_address()
            partner.geo_localize()
        except:
            _logger.info("There is an error during validate address.")
        finally:
            if partner.partner_longitude <= 0 and partner.partner_latitude <= 0:
                customer_lat_long = urllib.parse.quote("%s,%s,%s,%s,%s" % (partner.street, partner.zip, partner.city, partner.state_id.name or '', partner.country_id.name),safe="")
                map_url = "https://maps.googleapis.com/maps/api/directions/json?origin=52.53346639302402,13.059084762192581&destination=%s&key=%s" % (customer_lat_long, api_key)
                direction_data = self._get_direction(map_url)
                if direction_data.get("status") == "OK":
                    end_location = direction_data.get("routes")[0].get("legs")[0].get("end_location")
                    partner.write({'partner_latitude':end_location.get("lat",""),'partner_longitude':end_location.get("lng","")})

    @api.depends('user_id')
    def _compute_map_direction(self):
        for task in self:
            partner_id = task.user_id.partner_id
            related_vehicle = self.env['fleet.vehicle'].search([('driver_id', '=', partner_id.id)], limit=1)
            task.map_direction = ""
            approx_str = _("approx.")
            time_str = _("o'clock")

            if related_vehicle.bornemann_id:
                driver_lat_long = "%s,%s"%(related_vehicle.bornemann_partner_id.partner_latitude,related_vehicle.bornemann_partner_id.partner_longitude)
                google_map_key = self.env["ir.config_parameter"].sudo().get_param("google.map.key",default=False)
                if google_map_key:
                    try:
                        if not task.partner_id.partner_latitude or not task.partner_id.partner_longitude:
                            self.assign_partner_latlong(task.partner_id, google_map_key)
                        customer_lat_long = "%s,%s" % (task.partner_id.partner_latitude, task.partner_id.partner_longitude)
                        map_url = "https://maps.googleapis.com/maps/api/directions/json?origin=%s&destination=%s&key=%s"%(driver_lat_long,customer_lat_long, google_map_key)
                        direction_url = "https://www.google.com/maps/dir/%s/%s/@%s,12z"%(driver_lat_long, customer_lat_long, driver_lat_long)
                        direction_data = self._get_direction(map_url)
                        if direction_data.get("status") == "OK":
                            duration = direction_data.get("routes")[0].get("legs")[0].get("duration")
                            task.map_direction = "<a href='%s'>%s %s %s (%s)</a>" % (direction_url, approx_str, (fields.datetime.now() + timedelta(hours=2,seconds=duration.get("value"))).strftime("%H:%M"), time_str,self.display_time(duration.get("value")))
                        else:
                            task.map_direction = "<a href='#'>%s</a>"%(direction_data.get("error_message",_("No route found.")))
                    except Exception as e:
                        task.map_direction = "<a href='#'>%s</a>" % (str(e))
                else:
                    task.map_direction = "<a href='#'>Goog map API key not configured.</a>"


    @api.depends('effective_hours', 'subtask_effective_hours')
    def _compute_total_hours_spent(self):
        for task in self:
            task.total_hours_spent = task.effective_hours + task.subtask_effective_hours
            if task.sale_order_id:
                for line in task.sale_order_id.order_line:
                    if line.product_id.with_context(force_company=1).project_id and line.product_id.with_context(force_company=1).project_id.is_fsm:
                        line.product_uom_qty = task.total_hours_spent

    def _get_is_free_product(self):
        for this in self:
            this.is_free_products = False
            if this.free_products:
                this.is_free_products = True

    def _get_is_parameter_done(self):
        self.is_parameter_done = False
        for this in self:
            parameters = ['conductor_resistance', 'conductor_current', 'insulation_resistance', 'touch_current', 'water_conductor_resistance',
                             'water_hardness', 'water_total_hardness', 'full_demineralisation_conductance']
            for para in parameters:
                if getattr(this, para) and len(getattr(this, para)) > 0:
                    this.is_parameter_done = True
                    break

    def write(self, vals):
        result = super(ProjectTask, self).write(vals)
        for task in self:
            if task.sale_order_id:
                task.sale_order_id.asset_ids = [(6,0,task.asset_lines.ids)]
                required_prod = ""
                product_sku = []
                ap1_product_id = self.env['product.product'].search([('default_code', '=', 'GRIMM-AP001')], limit=1)
                ap2_product_id = self.env['product.product'].search([('default_code', '=', 'GRIMM-AP002')], limit=1)
                if task.driving_cost and ap1_product_id and ap2_product_id:
                    product_sku = task.sale_order_id.order_line.mapped('product_id.default_code')
                    ap1_line = task.sale_order_id.order_line.filtered(lambda r: r.product_id.id == ap1_product_id.id)
                    ap2_line = task.sale_order_id.order_line.filtered(lambda r: r.product_id.id == ap2_product_id.id)
                    if task.driving_cost == "ap001":
                        if ap1_line:
                            ap1_line.product_uom_qty = 1
                        else:
                            task.sale_order_id.write({"order_line":[(0,0,{"product_id":ap1_product_id.id,"product_uom_qty":1})]})
                        if ap2_line:
                            ap2_line.product_uom_qty = 0

                    elif task.driving_cost == "ap002":
                        if ap2_line:
                            ap2_line.product_uom_qty = task.driving_km
                        else:
                            task.sale_order_id.write({"order_line": [(0, 0, {"product_id": ap2_product_id.id, "product_uom_qty": task.driving_km})]})
                        if ap1_line:
                            ap1_line.product_uom_qty = 0
                else:
                    both_line = task.sale_order_id.order_line.filtered(lambda r: r.product_id.id in [ap1_product_id.id, ap2_product_id.id])
                    both_line.product_uom_qty = 0
        return result

    def roundTime(self, dt=None, roundTo=60):
        """Round a datetime object to any time lapse in seconds
        dt : datetime.datetime object, default now.
        roundTo : Closest number of seconds to round to, default 1 minute.
        """
        if dt == None: dt = datetime.now()
        seconds = (dt.replace(tzinfo=None) - dt.min).seconds
        rounding = (seconds + roundTo / 2) // roundTo * roundTo
        return dt + timedelta(0, rounding - seconds, -dt.microsecond)

    @api.onchange('planned_date_begin', 'planned_date_end')
    def onchange_planned_date(self):
        if self.planned_date_begin:
            self.planned_date_begin = self.roundTime(self.planned_date_begin, 900)
        if self.planned_date_end:
            self.planned_date_end =  self.roundTime(self.planned_date_end, 900)

    def action_next_state(self):
        self.stage_id=47

    def action_next_state_techniker(self):
        self.stage_id = 22

    def action_insert_free_product(self):
        default_value = {}
        default_value["default_task_id"] = self.id
        default_value["default_product_qty"] = ""
        default_value["default_product_price"] = ""

        return {
            'type': 'ir.actions.act_window',
            'name': _('Add Product'),
            'res_model': 'task.product.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': default_value,
            'views': [[False, 'form']]
        }

    def action_insert_parameter(self):
        default_value = {}
        default_value["default_task_ids"] = self.ids
        default_value["default_conductor_resistance"] = self.conductor_resistance
        default_value["default_conductor_current"] = self.conductor_current
        default_value["default_insulation_resistance"] = self.insulation_resistance
        default_value["default_touch_current"] = self.touch_current
        default_value["default_water_conductor_resistance"] = self.water_conductor_resistance
        default_value["default_water_hardness"] = self.water_hardness
        default_value["default_water_total_hardness"] = self.water_total_hardness
        default_value["default_full_demineralisation_conductance"] = self.full_demineralisation_conductance

        return {
            'type': 'ir.actions.act_window',
            'name': _('Parameter'),
            'res_model': 'project.task.parameter',
            'view_mode': 'form',
            'target': 'new',
            'context': default_value,
            'views': [[False, 'form']]
        }

    def get_backto_link(self, active_id=False):
        if active_id:
            href = active_id.get("href")
            start = "active_id="
            end = "&"
            res_id = (href.split(start))[1].split(end)[0]
            view_id = self.env.ref('grimm_fsm_extensions.grimm_fsm_project_task_form_view').id
            return {"res_id":int(res_id),"view_id":int(view_id)}
            #return "%s&action=%s"%(self.env['gteg.invoice.import']._compute_rec_link(res_id,self._name),self.env.ref('industry_fsm.project_task_action_fsm').id)
        return {}

    def _scheduler_task_due(self):
        due_tasks = self.env['project.task'].search([('date_deadline', '<', fields.Datetime.now()),('date_deadline', '!=', False)], )
        '''
        Need to group by project mannualy.
        '''
        project_tasks = {}
        for task in due_tasks:
            task_list = project_tasks.get(task.project_id.id, [])
            task_list.append(task)
            project_tasks[task.project_id.id] = task_list

        for project_id,tasks in project_tasks.items():
            table_str = "<br/><br/><table width='80%' align='center'><tr><th align='left'>Ticket #</th><th align='left'>Due Date</th></tr>"
            for task in tasks:
                table_str += "<tr><td align='left'><a href='%s&action=%s'>%s</a></td><td align='left'>%s</td></tr>"%(self.env['gteg.invoice.import']._compute_rec_link(task.id,task._name),self.env.ref('industry_fsm.project_task_action_fsm').id,task.name, task.date_deadline)
            table_str += "</table>"

            user_ids = [user for user in task.project_id.user_ids]
            if task.project_id.user_id:
                user_ids.append(task.project_id.user_id)
            user_ids = list(set(user_ids))
            vals = {'email_from': 'office@grimm-gastrobedarf.de',
                    'email_to': ",".join([str(u_id.email_formatted) for u_id in user_ids]),
                    'body_html': "Dear Manager,<br/>%s<br/>Thank you."%(table_str),
                    'type': 'email',
                    'subject': '%s : Due tasks on %s'%(task.project_id.name,fields.Datetime.now().date())}
            mail = self.env['mail.mail'].create(vals)
            mail.send()

    def action_send_report(self):
        self.ensure_one()
        result = super(ProjectTask, self).action_send_report()
        template_id = self.env.ref('grimm_fsm_extensions.grimm_fsm_mail_template_data_send_report').id
        result["context"]["default_template_id"] = template_id
        return result