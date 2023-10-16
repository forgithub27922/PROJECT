# -*- coding: utf-8 -*-


from odoo import fields, models


##############################################################################
#
# SaleLayoutCategory
#  - inherit
#
# @char     cat_name            interner Name der Kategorie
# @boolean  big_title           Titel im Großformat
# @boolean  pagebreak_before    Seitenumbruch davor
# @boolean  add_to_total        Positionskosten der Gesamtsumme hinzufügen
# @boolean  sub_counter         Separate Positionszählung
#
##############################################################################

class SaleLayoutCategory(models.Model):
    _name = 'sale.layout_category'
    _description = 'Sale layout category'
    _order = 'sequence, id'

    name = fields.Char('Name', required=True, translate=True)
    sequence = fields.Integer('Sequence', required=True, default=10)
    subtotal = fields.Boolean('Add subtotal', default=True)
    pagebreak = fields.Boolean('Add pagebreak')
    cat_name = fields.Char(string="Category Name", required=True)
    big_title = fields.Boolean(string="Big Title", default=False)
    pagebreak_before = fields.Boolean(string="Add pagebreak before", default=False)
    add_to_total = fields.Boolean(string="Add to total", default=True)
    sub_counter = fields.Boolean(string="Subcounter", default=False)
