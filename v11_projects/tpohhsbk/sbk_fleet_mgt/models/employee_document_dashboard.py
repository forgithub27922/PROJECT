# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import models, fields, api, _
from  datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo import tools


class Board(models.AbstractModel):
    _inherit = 'board.board'

    @api.model
    def default_get(self, fielslist):
        self.create_board_custom_view()
        return super(Board,self).default_get(fielslist)

    # @api.model
    # def load_views(self, views, options=None):
    #     res = super(Board,self).load_views(views,options)
    #     self.create_board_custom_view()
    #     return res

    @api.model
    def create_board_custom_view(self):
        view_id =  self.env.ref('sbk_fleet_mgt.emp_document_dashboard_form_view')
        if view_id:
            custom_view = self.env['ir.ui.view.custom'].sudo().search([('user_id', '=', self.env.uid), ('ref_id', '=', view_id.id)], limit=1)
            if not custom_view:
                custom_view = self.env['ir.ui.view.custom'].sudo().create({
                            'user_id': self.env.uid,
                            'ref_id': view_id.id,
                            'arch': view_id.arch
                        })

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        if view_type == 'form':
            self.create_board_custom_view()
        return super(Board, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)


class employee_visa_dashboard(models.Model):
    _name = 'employee.visa.dashboard'
    _auto = False

    employee_id = fields.Many2one('hr.employee',string="Employee")
    name = fields.Char(string="Name")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    @api.model
    def load_views(self, views, options=None):
        res = super(employee_visa_dashboard,self).load_views(views,options)
        self.update_dashboard_value()
        return res

    def update_dashboard_value(self):
        current_date = datetime.today().date().strftime(DF)
        month_start_date = (datetime.strptime(current_date, DF).replace(day=1))
        month_end_date = (month_start_date + relativedelta(months=+1, days=-1))
        month_start_date = month_start_date.strftime(DF)
        month_end_date = month_end_date.strftime(DF)
        company_id = self.env.user.company_id
        tools.drop_view_if_exists(self.env.cr, self._table)

        self._cr.execute("""
            CREATE OR REPLACE VIEW employee_visa_dashboard AS (
                SELECT id AS id,employee_id AS employee_id,name AS name,
                date_start AS start_date,date_end AS end_date
                FROM hr_visa WHERE active = 't' AND company_id = %s 
                AND date_end >= '%s' AND date_end <= '%s' ) """
                % (company_id.id,month_start_date,month_end_date))

    @api.model_cr
    def init(self):
        self.update_dashboard_value()


class employee_passport_dashboard(models.Model):
    _name = 'employee.passport.dashboard'
    _auto = False

    employee_id = fields.Many2one('hr.employee',string="Employee")
    name = fields.Char(string="Name")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    @api.model
    def load_views(self, views, options=None):
        res = super(employee_passport_dashboard,self).load_views(views,options)
        self.update_dashboard_value()
        return res

    def update_dashboard_value(self):
        current_date = datetime.today().date().strftime(DF)
        month_start_date = (datetime.strptime(current_date, DF).replace(day=1))
        month_end_date = (month_start_date + relativedelta(months=+1, days=-1))
        month_start_date = month_start_date.strftime(DF)
        month_end_date = month_end_date.strftime(DF)
        company_id = self.env.user.company_id

        tools.drop_view_if_exists(self.env.cr, self._table)

        self._cr.execute("""
            CREATE OR REPLACE VIEW employee_passport_dashboard AS (
                SELECT hr_doc.id AS id,hr_doc.employee_id AS employee_id,hr_doc.name AS name,
                hr_doc.date_start AS start_date,hr_doc.date_expiry AS end_date
                FROM hr_document hr_doc
                LEFT JOIN document_type dc_type ON dc_type.id = hr_doc.document_type_id 
                WHERE hr_doc.company_id = %s AND dc_type.type = 'passport' AND hr_doc.active = 't'
                AND hr_doc.date_expiry >= '%s' AND hr_doc.date_expiry <= '%s' ) """
                % (company_id.id,month_start_date,month_end_date))

    @api.model_cr
    def init(self):
        self.update_dashboard_value()
        

class employee_emirates_dashboard(models.Model):
    _name = 'employee.emirates.dashboard'
    _auto = False

    employee_id = fields.Many2one('hr.employee',string="Employee")
    name = fields.Char(string="Name")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    @api.model
    def load_views(self, views, options=None):
        res = super(employee_emirates_dashboard,self).load_views(views,options)
        self.update_dashboard_value()
        return res

    def update_dashboard_value(self):
        current_date = datetime.today().date().strftime(DF)
        month_start_date = (datetime.strptime(current_date, DF).replace(day=1))
        month_end_date = (month_start_date + relativedelta(months=+1, days=-1))
        month_start_date = month_start_date.strftime(DF)
        month_end_date = month_end_date.strftime(DF)
        company_id = self.env.user.company_id

        tools.drop_view_if_exists(self.env.cr, self._table)

        self._cr.execute("""
            CREATE OR REPLACE VIEW employee_emirates_dashboard AS (
                SELECT hr_doc.id AS id,hr_doc.employee_id AS employee_id,hr_doc.name AS name,
                hr_doc.date_start AS start_date,hr_doc.date_expiry AS end_date
                FROM hr_document hr_doc
                LEFT JOIN document_type dc_type ON dc_type.id = hr_doc.document_type_id 
                WHERE hr_doc.company_id = %s AND dc_type.type = 'emirates_id' AND hr_doc.active = 't'
                AND hr_doc.date_expiry >= '%s' AND hr_doc.date_expiry <= '%s' ) """
                % (company_id.id,month_start_date,month_end_date))

    def init(self):
        self.update_dashboard_value()
        

class employee_insurance_dashboard(models.Model):
    _name = 'employee.insurance.dashboard'
    _auto = False

    employee_id = fields.Many2one('hr.employee',string="Employee")
    name = fields.Char(string="Name")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    @api.model
    def load_views(self, views, options=None):
        res = super(employee_insurance_dashboard,self).load_views(views,options)
        self.update_dashboard_value()
        return res

    def update_dashboard_value(self):
        current_date = datetime.today().date().strftime(DF)
        month_start_date = (datetime.strptime(current_date, DF).replace(day=1))
        month_end_date = (month_start_date + relativedelta(months=+1, days=-1))
        month_start_date = month_start_date.strftime(DF)
        month_end_date = month_end_date.strftime(DF)
        company_id = self.env.user.company_id

        tools.drop_view_if_exists(self.env.cr, self._table)

        self._cr.execute("""
            CREATE OR REPLACE VIEW employee_insurance_dashboard AS (
                SELECT id AS id,employee_id AS employee_id,name AS name,
                from_date AS start_date,to_date AS end_date
                FROM hr_insurance WHERE company_id = %s 
                AND to_date >= '%s' AND to_date <= '%s' ) """
                % (company_id.id,month_start_date,month_end_date))

    @api.model_cr
    def init(self):
        self.update_dashboard_value()
        

class vehicle_registration_dashboard(models.Model):
    _name = 'vehicle.registration.dashboard'
    _auto = False

    vehicle_id = fields.Many2one('fleet.vehicle.model',string="Vehicle")
    name = fields.Char(string="Name")
    document_type_id = fields.Many2one('document.type',string="Document Type")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    @api.model
    def load_views(self, views, options=None):
        res = super(vehicle_registration_dashboard,self).load_views(views,options)
        self.update_dashboard_value()
        return res

    def update_dashboard_value(self):
        current_date = datetime.today().date().strftime(DF)
        month_start_date = (datetime.strptime(current_date, DF).replace(day=1))
        month_end_date = (month_start_date + relativedelta(months=+1, days=-1))
        month_start_date = month_start_date.strftime(DF)
        month_end_date = month_end_date.strftime(DF)
        company_id = self.env.user.company_id

        tools.drop_view_if_exists(self.env.cr, self._table)

        self._cr.execute("""
            CREATE OR REPLACE VIEW vehicle_registration_dashboard AS (
                SELECT id AS id,document_type_id AS document_type_id,name AS name,
                start_date AS start_date,expiry_date AS end_date,
                vehicle_id AS vehicle_id
                FROM fleet_vehicle_document WHERE company_id = %s 
                AND expiry_date >= '%s' AND expiry_date <= '%s' AND type = 'Registration' ) """
                % (company_id.id,month_start_date,month_end_date))

    @api.model_cr
    def init(self):
        self.update_dashboard_value()
        

class vehicle_insurance_dashboard(models.Model):
    _name = 'vehicle.insurance.dashboard'
    _auto = False

    vehicle_id = fields.Many2one('fleet.vehicle.model',string="Vehicle")
    name = fields.Char(string="Name")
    document_type_id = fields.Many2one('document.type',string="Document Type")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    @api.model
    def load_views(self, views, options=None):
        res = super(vehicle_insurance_dashboard,self).load_views(views,options)
        self.update_dashboard_value()
        return res

    def update_dashboard_value(self):
        current_date = datetime.today().date().strftime(DF)
        month_start_date = (datetime.strptime(current_date, DF).replace(day=1))
        month_end_date = (month_start_date + relativedelta(months=+1, days=-1))
        month_start_date = month_start_date.strftime(DF)
        month_end_date = month_end_date.strftime(DF)
        company_id = self.env.user.company_id

        tools.drop_view_if_exists(self.env.cr, self._table)

        self._cr.execute("""
            CREATE OR REPLACE VIEW vehicle_insurance_dashboard AS (
                SELECT id AS id,document_type_id AS document_type_id,name AS name,
                start_date AS start_date,expiry_date AS end_date,
                vehicle_id AS vehicle_id
                FROM fleet_vehicle_document WHERE company_id = %s 
                AND expiry_date >= '%s' AND expiry_date <= '%s' AND type = 'Insurance' ) """
                % (company_id.id,month_start_date,month_end_date))

    @api.model_cr
    def init(self):
        self.update_dashboard_value()
        

class company_document_dashboard(models.Model):
    _name = 'company.document.dashboard'
    _auto = False

    name = fields.Char(string="Name")
    document_type_id = fields.Many2one('document.type',string="Document Type")
    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    @api.model
    def load_views(self, views, options=None):
        res = super(company_document_dashboard,self).load_views(views,options)
        self.update_dashboard_value()
        return res

    def update_dashboard_value(self):
        current_date = datetime.today().date().strftime(DF)
        month_start_date = (datetime.strptime(current_date, DF).replace(day=1))
        month_end_date = (month_start_date + relativedelta(months=+1, days=-1))
        month_start_date = month_start_date.strftime(DF)
        month_end_date = month_end_date.strftime(DF)
        company_id = self.env.user.company_id.sudo()

        tools.drop_view_if_exists(self.env.cr, self._table)

        self._cr.execute("""
            CREATE OR REPLACE VIEW company_document_dashboard AS (
                SELECT id AS id,document_type_id AS document_type_id,name AS name,
                start_date AS start_date,expiry_date AS end_date
                FROM fleet_vehicle_document WHERE ref_company_id = %s 
                AND expiry_date >= '%s' AND expiry_date <= '%s' AND type = 'Company' ) """
                % (company_id.id,month_start_date,month_end_date))

    @api.model_cr
    def init(self):
        self.update_dashboard_value()