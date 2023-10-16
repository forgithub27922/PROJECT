# -*- coding: utf-8 -*-


from odoo import models, fields


class AssetLibrary(models.Model):
    _name = 'grimm.asset.library'
    _description = 'Asset Library'

    name = fields.Char(string='Name')
    matchcode = fields.Char(string='Match code', required=True)
    brand_id = fields.Many2one('grimm.product.brand', string='Brand')
    category_ids = fields.Many2many('grimm.asset.category', string='Categories')
    revision = fields.Char(string='Revision')
    exploded_drawing = fields.Binary('Exploded drawing')
    spare_parts_ids = fields.Many2many('product.product', 'grimm_asset_library_product_product_spare_parts_rel',
                                       'grimm_asset_library_id', 'product_product_id', string='Spare parts',
                                       domain=[('is_spare_part', '=', True)])
    tools_ids = fields.Many2many('product.product', 'grimm_asset_library_product_product_tools_rel',
                                 'grimm_asset_library_id', 'product_product_id', string='Tools',
                                 domain=[('is_tool', '=', True)])
    qualification_ids = fields.Many2many('grimm.asset.qualification', string='Qualifications')
    supplier_ids = fields.Many2many('res.partner', string='Suppliers',
                                    domain=[('supplier_rank', '>', 0)])
    width = fields.Float('Width')
    height = fields.Float('Height')
    length = fields.Float('Length')

    _sql_constraints = [
        ('match_code_uniq', 'unique(matchcode)', 'Matchcode must be unique !'),
    ]


class AssetCategory(models.Model):
    _name = 'grimm.asset.category'
    _description = 'Asset Category'

    name = fields.Char(string='Name')


class AssetQualification(models.Model):
    _name = 'grimm.asset.qualification'
    _description = 'Asset Qualification'

    name = fields.Char(string='Name')
    employee_ids = fields.One2many('hr.employee', 'qualification_id', string='Employees')
