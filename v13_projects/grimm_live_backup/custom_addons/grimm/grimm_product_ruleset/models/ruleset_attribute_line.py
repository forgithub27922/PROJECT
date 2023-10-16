# -*- coding: utf-8 -*-

from odoo import models, fields, api


class RulesetAttributeLine(models.Model):
    _name = 'ruleset.attribute.line'
    _description = 'Ruleset Attribute Line'

    sequence = fields.Integer("Sequence")
    property_id = fields.Many2one('property.set', string='Property')
    attribute_id = fields.Many2one('product.attribute', string='Attributes')
    ruleset_id = fields.Many2one('name.config.ruleset', string='Ruleset')
