from odoo import models, fields
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
import logging
_logger = logging.getLogger(__name__)


class OptionValue(models.Model):
    _name = 'grimm_custom_product.option_value'
    _description = 'Grimm Custom Product Option Value'

    name = fields.Char(required=True)

    use_product_data = fields.Boolean(default=True)
    use_product_price = fields.Boolean(default=True)
    sku = fields.Char()
    position = fields.Integer()
    price = fields.Float()

    option_id = fields.Many2one('grimm_custom_product.option', 'Template')
    product_id = fields.Many2one(comodel_name="product.template")

    shopware6_bind_ids = fields.One2many(
        comodel_name='shopware6.grimm_custom_product.option_value',
        inverse_name='openerp_id',
        string='Shopware6 Bindings',
    )
    is_shopware6_exported = fields.Boolean(string='Is Exported ?', compute='_get_is_shopware6_exported')

    def _get_is_shopware6_exported(self):
        for this in self:
            this.is_shopware6_exported = False
            for bind in this.shopware6_bind_ids:
                if bind.shopware6_id:
                    this.is_shopware6_exported = True

class CustomProductOptionValueShopware6(models.Model):
    _name = 'shopware6.grimm_custom_product.option_value'
    _inherit = 'shopware6.binding'
    _inherits = {'grimm_custom_product.option_value': 'openerp_id'}
    _description = 'Shopware6 Custom Product Option'

    _rec_name = 'backend_id'

    openerp_id = fields.Many2one(comodel_name='grimm_custom_product.option_value',
                                 string='Custom Product Option Value',
                                 required=True,
                                 ondelete='cascade')

class Shopware6BindingCustomProductOptionValueListener(Component):
    _name = 'shopware6.binding.custom.product.option.value.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['shopware6.grimm_custom_product.option_value']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        record.with_delay().export_record()

class Shopware6CustomProductOptionValueListener(Component):
    _name = 'custom.product.option.value.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['grimm_custom_product.option_value']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        for pp_bind in record.shopware6_bind_ids:
            pp_bind.with_delay().export_record(fields=fields)

class CustomProductOptionValueAdapter6(Component):
    _name = 'shopware6.grimm_custom_product.option.value.adapter'
    _inherit = 'shopware6.adapter'
    _apply_on = 'shopware6.grimm_custom_product.option_value'

    _shopware_uri = 'api/v3/swag-customized-products-template-option-value/'