# -*- encoding: utf-8 -*-
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
#

from odoo import api, fields, models, _


def _get_employee(self):
    request_link_obj = self.env['res.request.link']
    return [(res.object, res.name)
            for res in request_link_obj.search([
            ('object', 'in', ['hr.employee', 'hr.department'])])]


class AccountAssetAsset(models.Model):
    _inherit = 'account.asset.asset'

    department_id = fields.Many2one('hr.department', string='Department')
    recovery_amount = fields.Float('Recovery Amount')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    asset_history_ids = fields.One2many('assets.history', 'asset_id')
    asset_toggle = fields.Boolean(string="Asset Toggle")

    @api.multi
    def set_assign_realise(self):
        '''
        To set assign and release assets to Employee or Department
        :return: wizard
        '''
        if self.asset_toggle:
            history_ids = self.asset_history_ids.sorted(
                lambda x: x.id, reverse=True)
            if history_ids:
                history_ids[0].write({'end_date': fields.Date.today()})
                self.asset_toggle = False
            if self.employee_id.employee_asset_ids:
                asset_line = self.employee_id.employee_asset_ids.sorted(
                lambda x: x.id, reverse=True).filtered(
                    lambda x: x.asset_id.id == self.id)
                asset_line[0].recover_date = fields.Date.today()
            self.department_id = self.employee_id = False
            return True
        view_id = self.env.ref('bista_hr.wiz_view_asset_req')
        return {
            'name': 'Assign Request',
            'type': 'ir.actions.act_window',
            'view_id': view_id.id,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wiz.asset.request',
            'target': 'new',
        }


class EmployeeAssets(models.Model):
    _name = 'employee.assets'
    _description = "Employee Assets"

    asset_id = fields.Many2one('account.asset.asset', string='Asset')
    receive_date = fields.Date('Receive Date')
    recover_date = fields.Date('Recover Date')
    employee_id = fields.Many2one('hr.employee',
                                  string='Employee')
    department_id = fields.Many2one("hr.department", string='Department')
    penalties = fields.Float(string="Penalties")
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)


class AssetRequestWizard(models.TransientModel):
    _name = 'wiz.asset.request'

    date = fields.Date('Date', default=lambda d: fields.Date.today())
    emp_dept_id = fields.Reference(selection=_get_employee,
                                   string='Employee/Department')
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)

    @api.multi
    def assign_asset(self):
        """
        To set asset in employee assets and create line for assets history
        :return: True
        """
        self.ensure_one()
        asset_history = self.env['assets.history']
        emp_asset_obj = self.env['employee.assets']

        asset_rec = self.env[self._context.get('active_model')].browse(
            self._context.get('active_id'))
        # vals to create record for asset history
        vals = {
            'start_date': self.date,
            'asset_id': asset_rec.id
        }
        # vals to create record for employee held assets
        emp_ast_vals = {
            'receive_date': self.date,
            'asset_id': asset_rec.id,
            'employee_id': False,
        }
        if self.emp_dept_id._name == 'hr.employee':
            vals.update({'employee_id': self.emp_dept_id.id})
            asset_rec.employee_id = self.emp_dept_id.id
            emp_ast_vals['employee_id'] = self.emp_dept_id.id
        if self.emp_dept_id._name == 'hr.department':
            vals.update({'department_id': self.emp_dept_id.id})
            asset_rec.department_id = self.emp_dept_id.id
        asset_history.create(vals)
        emp_asset_obj.create(emp_ast_vals)
        asset_rec.asset_toggle = True
        return True


class AssetsHistory(models.Model):
    _name = 'assets.history'
    _description = "Employee Asset History"

    employee_id = fields.Many2one('hr.employee', string="Employee")
    department_id = fields.Many2one('hr.department', "Department")
    asset_id = fields.Many2one('account.asset.asset', string="Asset")
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.user.company_id)


class Employee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """
        Show employee based on company
        """
        if args is None:
            args = []
        if self.env.context and self.env.context.get('company_id',False):
            company_id = self.env.context.get('company_id', False)
            if company_id:
                emp_ids = self.env['hr.employee'].search(
                    [('company_id', '=', company_id)])
                # args = [('id', 'in', emp_ids.ids)]
                return emp_ids.name_get()
        return super(Employee, self).name_search(
            name=name, args=args, operator=operator, limit=limit)


class EmployeeDepartment(models.Model):
    _inherit = 'hr.department'

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """
        Show department based on company
        """
        if args is None:
            args = []
        if self.env.context and self.env.context.get('company_id',False):
            company_id = self.env.context.get('company_id', False)
            if company_id:
                dept_ids = self.env['hr.department'].search(
                    [('company_id', '=', company_id)])
                # args = [('id', 'in', dept_ids.ids)]
                return dept_ids.name_get()
        return super(EmployeeDepartment, self).name_search(
            name=name, args=args, operator=operator, limit=limit)
