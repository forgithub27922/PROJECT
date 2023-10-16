from odoo import fields, models

class ProductProduct(models.Model):
    _inherit = 'product.product'

    grimm_product_custom_product_template_id = fields.Many2one('grimm_custom_product.template', 'Template')
    grimm_custom_product_use_parent_template = fields.Boolean(default=True)

    grimm_product_custom_product_template_name = fields.Char(related="grimm_product_custom_product_template_id.name")
    grimm_product_custom_product_template_technical_name = fields.Char(related="grimm_product_custom_product_template_id.technical_name")
    grimm_product_custom_product_template_description = fields.Html(related="grimm_product_custom_product_template_id.description")
    grimm_product_custom_product_template_active = fields.Boolean(related="grimm_product_custom_product_template_id.active")
    grimm_product_custom_product_template_step_by_step_mode = fields.Boolean(related="grimm_product_custom_product_template_id.step_by_step_mode")
    grimm_product_custom_product_template_options_auto_collapse = fields.Boolean(related="grimm_product_custom_product_template_id.options_auto_collapse")
    grimm_product_custom_product_template_need_confirmation = fields.Boolean(related="grimm_product_custom_product_template_id.need_confirmation")
    grimm_product_custom_product_template_image = fields.Image(related="grimm_product_custom_product_template_id.image")
    grimm_product_custom_product_template_option_ids = fields.One2many(related="grimm_product_custom_product_template_id.option_ids")