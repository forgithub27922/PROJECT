# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class RolePartner(models.Model):
    _name = 'crm.claim.role_partner'
    _description = 'Claim Role Partner'
    _order = 'name'

    name = fields.Char('Name', index=True)


class CrmClaim(models.Model):
    _inherit = 'crm.claim'

    @api.model
    def _default_sale_team(self):
        sale_team = self.env['crm.team'].search([('name', 'ilike', 'Service')])
        if sale_team:
            return sale_team.id

    asset_id = fields.Many2one('grimm.asset.asset', string='Asset', index=True)
    asset_name = fields.Char(related='asset_id.name')
    asset_serial = fields.Char(related='asset_id.serial_number')
    asset_default_code = fields.Char(related='asset_id.default_code')
    asset_customer_inventory_no = fields.Char(related='asset_id.customer_inventory_no')
    asset_concat_name = fields.Char(string='Asset Name', compute='_compute_string', store="True")
    asset_address = fields.Many2one(related='asset_id.partner_contact')
    asset_object = fields.Many2one(related='asset_id.asset_facility_id')
    create_user = fields.Char(related='create_uid.name')
    product_id = fields.Many2one('product.template', string='Product',
                                 ondelete='restrict', index=True)
    brand_name = fields.Char(string="Brand Name", related='asset_id.brand', readonly=True)
    brand_id = fields.Many2one('res.partner', string="Brand Partner")
    brand_contact = fields.Many2one('res.partner', string="Brand Partner",
                                    domain="[('parent_id', '=', self.brand_id),('type','like','contact')]")
    brand_phone = fields.Char(related='brand_id.phone', store=True)
    brand_mobile = fields.Char(related='brand_id.mobile', store=True)
    brand_email = fields.Char(related='brand_id.email', store=True)
    task_ids = fields.One2many('project.task', 'claim_id', string='Task')
    sale_order_count = fields.Integer(
        compute='_compute_sale_order_count', string='# of Sales Order')
    mrp_repair_count = fields.Integer(
        compute='_compute_mrp_repair_count', string='# of Repairs')
    project_task_count = fields.Integer(
        compute='_compute_project_task_count', string='# of Tasks')
    sequence = fields.Char(string="Claim Reference", required=True, copy=False,
                           stage_ids={'draft': [('readonly', False)]}, readonly=True, index=True,
                           default=lambda self: _('New'))
    owner = fields.Many2one('res.partner', related='asset_id.partner_owner', string='Owner')
    beneficiary = fields.Many2one(
        'res.partner', related='asset_id.beneficiary', string='Beneficiary')
    customer_ref = fields.Char(string='Reference')
    partner_mobile = fields.Char(related='partner_id.mobile', store=True, string='Mobile')
    user_id = fields.Many2one('res.users', 'Responsible', track_visibility='always', default=False)
    team_id = fields.Many2one('crm.team', 'Sales Team',
                              index=True, help="Responsible sales team."
                                                " Define Responsible user and Email account for"
                                                " mail gateway.", default=_default_sale_team)
    asset_internal_cat = fields.Char(related='asset_id.internal_cat', readonly=True)
    asset_invoice_partner = fields.Many2one(related='asset_id.partner_invoice', readonly=True)
    asset_delivery_partner = fields.Many2one(related='asset_id.partner_delivery', readonly=True)
    role_partner = fields.Many2one(comodel_name='crm.claim.role_partner', string="Rollenpartner")

    # change name output to claim sequence
    def name_get(self):
        res = []
        for claim in self:
            res.append((claim.id, str(claim.sequence)))

        return res

    def create_saleorder(self):
        ctx = self._context.copy()
        if self.asset_id.id:
            ctx.update({'default_asset_ids': [(6, 0, [self.asset_id.id])]})
        if self.partner_id:
            ctx.update({'default_partner_id': self.asset_address.id or self.partner_id.id})
        if self.partner_id.property_payment_term_id:
            ctx.update({'default_prepayment': False})
            ctx.update({'default_payment_term_id': self.partner_id.property_payment_term_id.id})
        if self.partner_id.customer_payment_mode_id:
            ctx.update({'default_payment_mode_id': self.partner_id.customer_payment_mode_id.id})
        if self.asset_id.asset_facility_id:
            ctx.update({'default_object_address': self.asset_id.asset_facility_id.id})
        if self.asset_invoice_partner:
            ctx.update({'default_partner_invoice_id': self.asset_invoice_partner.id})
        if self.asset_delivery_partner:
            ctx.update({'default_partner_shipping_id': self.asset_delivery_partner.id})
        if self.name:
            ctx.update({'default_order_subject': self.name})
        if self.beneficiary:
            ctx.update({'default_beneficiary': self.beneficiary.id})
        if self.customer_ref:
            ctx.update({'default_client_order_ref': self.customer_ref})
        if self.owner:
            ctx.update({'default_contact': self.partner_id.id})
        if self.asset_address:
            ctx.update({'default_contact': self.asset_address.id})
        if self.id:
            ctx.update({'default_claim_id': self.id})
        analytic_account_id = self.env['hr.employee'].search(
            [('id', '=', self.user_id.id)])
        ctx.update({'default_team_id': self.team_id.id})
        # ctx.update({'default_analytic_account_id': analytic_account_id.department_id.analytic_id.id}) Odoo13Change

        ctx.update({'search_default_claim_id': self.id})
        ctx.pop('group_by', None)
        print(ctx)

        form_view_id = self.env.ref('sale.view_order_form')
        tree_view_id = self.env.ref('sale.view_quotation_tree')
        result = {
            'name': _('Quotations'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'views': [(tree_view_id.id or False, 'tree'),
                      (form_view_id.id or False, 'form')],
            'target': 'current',
            'context': ctx,
        }
        return result

    def create_task(self):
        ctx = self._context.copy()
        if self.asset_id.id:
            ctx.update({'default_asset_ids': [(6, 0, [self.asset_id.id])]})
        if self.partner_id:
            ctx.update({'default_partner_id': self.partner_id.id})
        if self.name:
            ctx.update({'default_order_subject': self.name})
        if self.beneficiary:
            ctx.update({'default_beneficiary': self.beneficiary.id})
        if self.owner:
            ctx.update({'default_contact': self.owner.id})
        if self.id:
            ctx.update({'default_claim_id': self.id})

        ctx.update({'search_default_claim_id': self.id})
        #related_tasks = self.env['project.task'].search([['claim_id', 'in', self.ids]])

        form_view_id = self.env.ref('project.view_task_form2')
        tree_view_id = self.env.ref('project.view_task_tree2')
        result = {
            'name': _('Tasks'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'project.task',
            #"domain": [["id", "in", related_tasks.ids]],
            'views': [
                (tree_view_id.id or False, 'tree'),
                (form_view_id.id or False, 'form')],
            'context': ctx,
        }
        return result

    def _compute_string(self):
        for record in self:
            record.asset_concat_name = (record.asset_name or '') + ' ' + \
                                       (record.asset_serial or '') + ' ' + (record.asset_default_code or '')

    def _compute_sale_order_count(self):
        for record in self:
            record.sale_order_count = self.env['sale.order'].search_count(
                [('asset_ids', 'in', record.id)])

    def _compute_mrp_repair_count(self):
        for record in self:
            record.mrp_repair_count = self.env['repair.order'].search_count(
                [('asset_id', '=', record.id)])

    def _compute_project_task_count(self):
        for record in self:
            record.project_task_count = self.env['project.task'].search_count(
                [('asset_ids', 'in', record.id)])

    @api.model
    def create(self, vals):
        if vals.get('sequence', 'New') == 'New':
            vals['sequence'] = self.env['ir.sequence'].next_by_code('crm.claim') or 'New'
        return super(CrmClaim, self).create(vals)

    @api.onchange('categ_id')
    def _onchange_categ_id(self):
        if self.stage_id.name in ['new', 'Neu']:
            self.stage_id = 2
            self.write({'stage_id': 2})

    @api.onchange('brand_id')
    def _onchange_brand_id(self):
        if self.brand_id:
            self.brand_contact = self.brand_id.email or False

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            if self.partner_id.phone:
                self.partner_phone = self.partner_id.phone
            if self.partner_id.email:
                self.email_from = self.partner_id.email

        if self.asset_id:
            asset_id = self.asset_id
            if self.partner_id == asset_id.partner_contact:
                self.product_id = self.asset_id.product_id
            else:
                self.asset_id = False

    @api.onchange('asset_id')
    def _onchange_asset_id(self):
        if self.asset_id:
            self.product_id = self.asset_id.product_id
        else:
            self.product_id = False
        if self.asset_address:
            self.partner_id = self.asset_address
