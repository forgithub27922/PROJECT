from odoo import models, fields
from odoo.addons.component.core import Component
from odoo.addons.component_event import skip_if
import logging
_logger = logging.getLogger(__name__)


class option(models.Model):
    _name = 'grimm_custom_product.option'
    _description = 'Grimm Custom Product Option'

    name = fields.Char(required=True)
    type = fields.Selection(
        [
            ('checkbox', 'Checkbox'),
            ('select', 'Select')
        ],
        'Type',
        default='checkbox',
        required=True
    )
    description = fields.Html()
    image = fields.Image()
    required = fields.Boolean("Required")

    template_id = fields.Many2one('grimm_custom_product.template', 'Template')
    values = fields.One2many('grimm_custom_product.option_value', 'option_id')
    value = fields.Many2one('grimm_custom_product.option_value', 'option_id')

    multiselect = fields.Boolean()

    min_qty = fields.Integer(default=1)
    max_qty = fields.Integer(default=10)

    sequence = fields.Integer('sequence', help="Sequence for the handle.", default=10)
    shopware6_bind_ids = fields.One2many(
        comodel_name='shopware6.grimm_custom_product.option',
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


class CustomProductOptionShopware6(models.Model):
    _name = 'shopware6.grimm_custom_product.option'
    _inherit = 'shopware6.binding'
    _inherits = {'grimm_custom_product.option': 'openerp_id'}
    _description = 'Shopware6 Custom Product Option'

    _rec_name = 'backend_id'

    openerp_id = fields.Many2one(comodel_name='grimm_custom_product.option',
                                 string='Custom Product Option',
                                 required=True,
                                 ondelete='cascade')

class Shopware6BindingCustomProductOptionListener(Component):
    _name = 'shopware6.binding.custom.product.option.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['shopware6.grimm_custom_product.option']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_create(self, record, fields=None):
        record.export_record()

class Shopware6CustomProductOptionListener(Component):
    _name = 'custom.product.option.listener'
    _inherit = 'base.connector.listener'
    _apply_on = ['grimm_custom_product.option']

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_write(self, record, fields=None):
        for pp_bind in record.shopware6_bind_ids:
            pp_bind.with_delay().export_record(fields=fields)

    @skip_if(lambda self, record, **kwargs: self.no_connector_export(record))
    def on_record_unlink(self, record):
        for rec in record.shopware6_bind_ids:
            rec.with_delay().export_delete_record(rec.backend_id, rec.shopware6_id)

class CustomProductOptionAdapter6(Component):
    _name = 'shopware6.grimm_custom_product.option.adapter'
    _inherit = 'shopware6.adapter'
    _apply_on = 'shopware6.grimm_custom_product.option'

    _shopware_uri = 'api/v3/swag-customized-products-template-option/'


