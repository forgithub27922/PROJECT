# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ProjectTask(models.Model):
    _inherit = "project.task"

    asset_ids = fields.Many2many('grimm.asset.asset', string='Asset')
    #mro_order_id = fields.Many2one('grimm.mro.order', string='MRO Order')
    mrp_repair_id = fields.Many2one('repair.order', string='Repair')
    name_seq = fields.Char(string='Task Code', required=True, copy=False, default='/')
    claim_id = fields.Many2one('crm.claim', string='Claim')
    claim_name = fields.Char(related='claim_id.name')
    claim_sequence = fields.Char(related='claim_id.sequence')
    claim_contact = fields.Many2one('res.partner', string='Contact', default=lambda self: self._get_default_contact())
    claim_contact_mobile = fields.Char('Mobile')
    claim_contact_phone = fields.Char('Phone')
    claim_contact_email = fields.Char('E-Mail')
    claim_categ_id = fields.Many2one(comodel_name='crm.claim.category', string='Category',
                                     compute='compute_claim_category', store=True)
    location_ids = fields.One2many(related='asset_ids.location_ids')
    claim_shipping_id = fields.Many2one('res.partner', string="Shipping Address")
    asset_internal_cat = fields.Char(related='asset_ids.internal_cat')
    name = fields.Char(default=lambda self: self._get_default_task_title())

    @api.model
    def _get_default_task_title(self):
        """
        set default title for project.task
        if no claim_id is given, the title will be an empty string
        :return:
        """
        default_claim_id = self._context.get('default_claim_id', False)
        if default_claim_id:
            claim = self.env['crm.claim'].browse(default_claim_id)
            if claim and claim.name:
                return claim.name
        return ''

    @api.model
    def _get_default_contact(self):
        """
        set default title for project.task
        if no claim_id is given, the contact will be empty
        :return:
        """
        default_claim_id = self._context.get('default_claim_id', False)
        if default_claim_id:
            try:
                claim = self.env['crm.claim'].browse(default_claim_id)
                if claim.partner_id:
                    return claim.partner_id
            except:
                pass
        return ''

    @api.depends('claim_id')
    def compute_claim_category(self):
        for record in self:
            if record.claim_id and record.claim_id.categ_id:
                record.claim_categ_id = record.claim_id.categ_id

    @api.onchange('partner_id')
    def onchange_partner_id_grimm(self):
        for task in self:
            if task.partner_id:
                delivery_partners = self.env['res.partner'].search([['type', '=', 'delivery'],
                                                                    ['parent_id', '=', task.partner_id.id]])
                for delivery_partner in delivery_partners:
                    task.claim_shipping_id = delivery_partner
                    break

                contact_partners = self.env['res.partner'].search([['type', '=', 'contact'],
                                                                   ['parent_id', '=', task.partner_id.id]])
                for contact in contact_partners:
                    task.claim_contact = contact
                    break

    @api.onchange('partner_id', 'claim_contact')
    def onchange_partner_id_claim_contact(self):
        for record in self:
            contact = record.claim_contact
            if not contact and record.partner_id:
                contact = record.partner_id
            if contact:
                record.claim_contact_mobile = contact.mobile
                record.claim_contact_phone = contact.phone
                record.claim_contact_email = contact.email

    @api.model
    def create(self, vals):
        claim = ""
        vals['name_seq'] = self.env['ir.sequence'].next_by_code('project.task.seq')
        if 'procurement_id' in vals:
            procurement_id = self.env['procurement.order'].search(
                [('id', '=', vals['procurement_id'])], limit=1)
            partner_shipping_id = procurement_id.sale_line_id.order_id.partner_shipping_id.id
            contact_id = self.env['procurement.order'].search(
                [('id', '=', vals['procurement_id'])], limit=1).sale_line_id.order_id.contact.id
            vals['claim_shipping_id'] = partner_shipping_id
            vals['claim_contact'] = contact_id
        if 'claim_id' in vals:
            claim = self.env['crm.claim'].search([('id', '=', vals['claim_id'])]).sequence
        elif self.claim_id:
            claim = self.env['crm.claim'].search([('id', '=', self.claim_id)]).sequence
        if not claim:
            claim = '00000'
            vals['name'] = '%s-%s' % (claim, vals['name_seq'])
        res =  super(ProjectTask, self).create(vals)
        if getattr(res.project_id, 'is_fsm', False):
            subject = ""
            if res.sale_line_id and res.sale_line_id.order_id.order_subject:
                subject = res.sale_line_id.order_id.order_subject
            res.name = '%s %s' % ((vals['name_seq']), subject)
        return res
    #
    # @api.model
    # def action_delegate_task_2_user(self):
    #     if self:
    #         self.copy()
    #     return super(ProjectTask, self).action_delegate_task_2_user()
