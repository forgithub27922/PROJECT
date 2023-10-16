# -*- coding: utf-8 -*-

from odoo.osv import expression
from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    l10n_mx_edi_usage = fields.Selection(
        selection=[
            ('G01', '[G01] Acquisition of merchandise'),
            ('G02', '[G02] Returns, discounts or bonuses'),
            ('G03', '[G03] General expenses'),
            ('I01', '[I01] Constructions'),
            ('I02', '[I02] Office furniture and equipment investment'),
            ('I03', '[I03] Transportation equipment'),
            ('I04', '[I04] Computer equipment and accessories'),
            ('I05', '[I05] Dices, dies, molds, matrices and tooling'),
            ('I06', '[I06] Telephone communications'),
            ('I07', '[I07] Satellite communications'),
            ('I08', '[I08] Other machinery and equipment'),
            ('D01', '[D01] Medical, dental and hospital expenses.'),
            ('D02', '[D02] Medical expenses for disability'),
            ('D03', '[D03] Funeral expenses'),
            ('D04', '[D04] Donations'),
            ('D05', '[D05] Real interest effectively paid for mortgage loans (room house)'),
            ('D06', '[D06] Voluntary contributions to SAR'),
            ('D07', '[D07] Medical insurance premiums'),
            ('D08', '[D08] Mandatory School Transportation Expenses'),
            ('D09', '[D09] Deposits in savings accounts, premiums based on pension plans.'),
            ('D10', '[D10] Payments for educational services (Colegiatura)'),
            ('P01', '[P01] To define'),
        ],
        string="Usage",
        default='P01',
        help="Used in CFDI 3.3 to express the key to the usage that will gives the receiver to this invoice. This "
             "value is defined by the customer.\nNote: It is not cause for cancellation if the key set is not the usage "
             "that will give the receiver of the document.", tracking=True, change_default=True)
    l10n_mx_edi_payment_method_id = fields.Many2one('l10n_mx_edi.payment.method',
        string="Payment Way",
        help="Indicates the way the invoice was/will be paid, where the options could be: "
             "Cash, Nominal Check, Credit Card, etc. Leave empty if unkown and the XML will show 'Unidentified'.",
        default=lambda self: self.env.ref('l10n_mx_edi.payment_method_otros', raise_if_not_found=False), 
        tracking=True, change_default=True)
    l10n_mx_edi_payment_policy = fields.Selection(string='Payment Policy',
        selection=[('PPD', 'PPD'), ('PUE', 'PUE')], default='PPD', 
        tracking=True, change_default=True)

    l10n_mx_edi_payment_policy = fields.Selection(string='Payment Policy',
        selection=[('PPD', 'PPD'), ('PUE', 'PUE')])


class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_mx_edi_payment_policy = fields.Selection(string='Payment Policy',
        selection=[('PPD', 'PPD'), ('PUE', 'PUE')],
        readonly=False, store=True, tracking=True, change_default=True)
    # invoice_payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms', check_company=True, readonly=False, states={})

    # -------------------------------------------------------------------------
    # Account invoice methods
    # -------------------------------------------------------------------------
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        res = super(AccountMove, self)._onchange_partner_id()
        self.l10n_mx_edi_usage = self.commercial_partner_id.l10n_mx_edi_usage
        self.l10n_mx_edi_payment_method_id = self.commercial_partner_id.l10n_mx_edi_payment_method_id
        self.l10n_mx_edi_payment_policy = self.commercial_partner_id.l10n_mx_edi_payment_policy
        return res

    @api.depends('move_type', 'invoice_date_due', 'invoice_date', 'invoice_payment_term_id', 'invoice_payment_term_id.line_ids')
    def _compute_l10n_mx_edi_payment_policy(self):
        for move in self:
            if move.l10n_mx_edi_payment_policy:
                move.l10n_mx_edi_payment_policy
        return ''

"""
class PaymentMethod(models.Model):
    _inherit = 'l10n_mx_edi.payment.method'

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', '=ilike', name.split(' ')[0] + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        method_ids = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return models.lazy_name_get(self.browse(method_ids).with_user(name_get_uid))

    def name_get(self):
        result = []
        for account in self:
            name = account.code + ' ' + account.name
            result.append((account.id, name))
        return result
"""

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _prepare_invoice(self):
        invoice_vals = super(PurchaseOrder, self)._prepare_invoice()
        invoice_vals['invoice_payment_term_id'] = self.payment_term_id and self.payment_term_id.id or self.partner_id.property_supplier_payment_term_id.id or False
        return invoice_vals
