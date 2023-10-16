# -*- coding: utf-8 -*-

from odoo import fields, models


class ReturnInstruction(models.Model):
    _name = "return.instruction"
    _description = 'Return Instructions'
    _description = "Instructions for product return"

    name = fields.Char('Title', required=True)
    instructions = fields.Text(
        'Instructions',
        help="Instructions for product return")
    is_default = fields.Boolean('Is default',
                                help="If is default, will be use "
                                     "to set the default value in "
                                     "supplier infos. Be careful to "
                                     "have only one default")
