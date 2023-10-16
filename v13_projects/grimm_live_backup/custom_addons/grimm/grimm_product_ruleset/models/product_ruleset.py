# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import random
import logging

_logger = logging.getLogger(__name__)


class NameConfigRuleset(models.Model):
    _name = 'name.config.ruleset'
    _description = 'Name Config Ruleset'

    name = fields.Char('Name', required=True)
    property_id = fields.Many2one('property.set', string='Property Set')
    attribute_line_ids = fields.One2many('ruleset.attribute.line', 'ruleset_id', string='Attributes', copy=True, ondelete='cascade')
    max_length = fields.Integer('Max Length')
    delimiter = fields.Char('Delimiter')
    append_company_name = fields.Boolean('Append Company Name')
    append_call_action = fields.Boolean('Append Call to Action')

    @api.onchange('property_id')
    def _onchange_property_id(self):
        self.attribute_line_ids = self.env['ruleset.attribute.line'].search([('property_id', '=', self.property_id.id),
                                                                             ('ruleset_id', '=', False)])

    def write(self, vals):
        if 'attribute_line_ids' in vals:
            i = 0
            while i < len(vals['attribute_line_ids']):
                if vals['attribute_line_ids'][i][0] == 1 or vals['attribute_line_ids'][i][0] == 4:
                    vals['attribute_line_ids'][i][0] = 1
                    vals['attribute_line_ids'][i][2] = {'sequence': i}
                elif vals['attribute_line_ids'][i][0] == 0:
                    attr_id = vals['attribute_line_ids'][i][2]['attribute_id']
                    vals['attribute_line_ids'][i][2] = {'sequence': i, 'attribute_id': attr_id}

                i += 1

        return super(NameConfigRuleset, self).write(vals)


class TemplateRuleset(models.Model):
    _inherit = 'product.template'

    prod_name = fields.Char('Product Name')
    ruleset_id = fields.Many2one('name.config.ruleset', string='Ruleset Product Description',
                                 domain="[('property_id', '=', property_set_id)]")
    ruleset_id_mt = fields.Many2one('name.config.ruleset', string='Ruleset Meta Title',
                                    domain="[('property_id', '=', property_set_id)]")
    ruleset_id_md = fields.Many2one('name.config.ruleset', string='Ruleset Meta Description',
                                 domain="[('property_id', '=', property_set_id)]")
    ruleset_id_prod = fields.Many2one('name.config.ruleset', string='Ruleset Product Name',
                                    domain="[('property_id', '=', property_set_id)]")

    def ruleset(self, ruleset_id, tmpl_id, shopware_property_ids):
        prod_prod = self.env['product.product'].search([('product_tmpl_id', '=', tmpl_id)], limit=1)
        ruleset_rec = self.env['ruleset.attribute.line'].search([('ruleset_id', '=', ruleset_id.id)])
        # print(self.shopware_property_ids)
        res_fitered_lst = []
        delimiter = ruleset_id.delimiter if ruleset_id.delimiter else ''
        sorted_attr_line = ruleset_rec.sorted(key=lambda s: s.sequence)
        for rul in sorted_attr_line:
            if rul.attribute_id.attr_type in ['char', 'integer', 'float']:
                for rec in shopware_property_ids:
                    if rul.attribute_id.id == rec.attribute_id.id:
                        res_fitered_lst.append(delimiter.join([attr_val.name for attr_val in rec.value_ids]))
            elif rul.attribute_id.attr_type == 'entity':
                # Note: We have to create seller_ids. If we don't set any value to Entity field and if we select type as entity, then it gets the value from seller_ids
                # The condition is that we are filtering out all the records with GRIMM as vendor
                filtered_prod_code_rec = prod_prod.sudo().seller_ids.search(
                    [('name', 'not in', [1, 83602, 7393, 9567, 33147, 14655, 24357, 24404]),
                     ('product_tmpl_id', '=', tmpl_id)], limit=1)
                try:
                    res_fitered_lst.append(eval('prod_prod.' + str(rul.attribute_id.entity_id.name) + '.name')
                                           if rul.attribute_id.entity_id else str(filtered_prod_code_rec.product_code))
                except:
                    res_fitered_lst.append(eval('prod_prod.' + str(rul.attribute_id.entity_id.name))
                                           if rul.attribute_id.entity_id else str(filtered_prod_code_rec.product_code))
            else:
                res_fitered_lst.append(rul.attribute_id.content)

        res_fitered_lst = list(filter(None, res_fitered_lst))

        ruleset_description = delimiter.join(res_fitered_lst)

        firm_name_long, firm_name_short = '| Partenics GmbH', '| PARTENICS'

        actions = ['Jetzt online bestellen!', 'Günstig online kaufen!', 'Jetzt online kaufen!',
                   'Preiswert online bestellen!', 'Online beim Fachhändler bestellen!',
                   'Bei PARTENICS online kaufen!', 'Schneller Versand - Jetzt bestellen!']
        action = delimiter + actions[random.randint(0, 6)] if ruleset_id.append_call_action else ''

        max_len = len(
            ruleset_description + delimiter + firm_name_long + action) if ruleset_id.max_length == 0 else ruleset_id.max_length

        if len(ruleset_description + delimiter + firm_name_long + action) <= max_len:
            company = delimiter + firm_name_long if ruleset_id.append_company_name else ''
            ruleset_description = ruleset_description + company + action
        elif len(ruleset_description + delimiter + firm_name_short + action) <= max_len:
            company = delimiter + firm_name_short if ruleset_id.append_company_name else ''
            ruleset_description = ruleset_description + company + action
        else:
            comp_action_str = delimiter + firm_name_short + action
            slicing_limit = max_len - len(comp_action_str)
            ruleset_description = ruleset_description[:slicing_limit] + comp_action_str

        return ruleset_description

    @api.onchange('ruleset_id')
    def _onchange_ruleset_id(self):
        self.shopware_description = self.ruleset(self.ruleset_id, self._origin.id,
                                                 self.shopware_property_ids) if self.ruleset_id else False

    @api.onchange('ruleset_id_mt')
    def _onchange_ruleset_id_mt(self):
        self.shopware_meta_title = self.ruleset(self.ruleset_id_mt, self._origin.id,
                                                self.shopware_property_ids) if self.ruleset_id_mt else False

    @api.onchange('ruleset_id_prod')
    def _onchange_ruleset_id_prod(self):
        prod_rul_val = self.ruleset(self.ruleset_id_prod, self._origin.id,
                                    self.shopware_property_ids) if self.ruleset_id_prod else False
        self.prod_name = prod_rul_val
        self.generate_ebay_title = prod_rul_val

    @api.onchange('ruleset_id_md')
    def _onchange_ruleset_id_md(self):
        self.shopware_meta_description = self.ruleset(self.ruleset_id_md, self._origin.id,
                                                      self.shopware_property_ids) if self.ruleset_id_md else False

    @api.onchange('shopware_property_ids')
    def onchange_shopware_property_ids(self):
        for attr in self.shopware_property_ids:
            try:
                for rec in attr.value_ids:
                    if rec.name.isdigit():
                        pass
                    elif type(float(rec.name)) is float:
                        pass
            except:
                if attr.attribute_id.attr_type in ['integer', 'float']:
                    raise UserError(_('String values cannot be added to the attribute %s') % attr.attribute_id.name)

    def write(self, vals):
        if 'property_set_id' in vals:
            for rec in self:
                shopware_property_line_count = self.env['shopware.property.line'] \
                    .search([('product_tmpl_id', '=', rec.id)])
                shopware_property_line_count.unlink()
                vals.update({'ruleset_id': False, 'ruleset_id_mt': False, 'ruleset_id_md': False, 'ruleset_id_prod': False})

        return super(TemplateRuleset, self).write(vals)
