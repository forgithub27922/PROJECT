from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class PackProd(models.Model):
    _inherit = 'product.template'

    pack_products = fields.Html('Pack Products', compute='_concat_pack_products')
    stock_locations = fields.Char('Stock Locations', compute='_concat_stock_locations')

    def _concat_pack_products(self):
        for rec in self:
            prod = self.browse(rec.id)
            if prod.pack_ids:
                html_text = ''
                for pack in prod.pack_ids:
                    html_text += '<li>' + pack.product_id.name + ' (' + str(pack.qty_uom) + ')</li>'

                rec.pack_products = '<ul style="margin-bottom: 0px; padding-left: 0px;">' + html_text + '</ul>'
            else:
                rec.pack_products = ''

    def _concat_stock_locations(self):
        for rec in self:
            prod_id = self.env['product.product'].search([('product_tmpl_id', '=', rec.id)], limit=1).id
            stock_quant_rec = self.env['stock.quant'].with_context(lang=self.env.user.lang).search(
                [('product_id', '=', prod_id), ('company_id', '=', self.env.user.company_id.id)])
            if stock_quant_rec:
                rec.stock_locations = ', '.join(
                    [rec_stock.location_id.name for rec_stock in stock_quant_rec if rec_stock.location_id])
            else:
                rec.stock_locations = ''

    def set_on_spare_parts(self, products):
        for prod in products:
            for spare_part in prod.spare_part_ids:
                update_sparepart = {}
                if prod.shopware_categories != spare_part.shopware_categories:
                    lst_cat = []
                    for rec in prod.shopware_categories:
                        if rec.id not in [childs.id for childs in spare_part.shopware_categories]:
                            child_ids = [childs.id for childs in spare_part.shopware_categories]
                            child_ids.append(rec.id)
                            lst_cat.append((6, 0, child_ids))

                    update_sparepart.update({'shopware_categories': lst_cat})

                if not spare_part.property_set_id:
                    update_sparepart.update({'property_set_id': prod.property_set_id.id})
                    avail_property = prod.property_set_id
                else:
                    avail_property = spare_part.property_set_id

                spare_attr = avail_property.product_attribute_ids.filtered(
                    lambda r: r.technical_name in ['sw_geraeteart', 'sw_modell']).sorted(key=lambda r: r.name)

                if spare_part.shopware_property_ids:
                    mother_attr = prod.shopware_property_ids.filtered(
                        lambda r: r.attribute_id.technical_name in ['sw_geraeteart', 'sw_modell']).sorted(
                        key=lambda r: r.attribute_id.name)
                    child_attr = spare_part.shopware_property_ids.filtered(
                        lambda r: r.attribute_id.technical_name in ['sw_geraeteart', 'sw_modell']).sorted(
                        key=lambda r: r.attribute_id.name)
                    lst_attr = []
                    for rec in mother_attr:
                        if rec.attribute_id.id not in [attr.attribute_id.id for attr in
                                                       child_attr] and rec.attribute_id.id in [sp_attr.id for sp_attr in
                                                                                               spare_attr]:
                            lst_attr.append(
                                (0, 0, dict(attribute_id=rec.attribute_id.id, value_ids=[(6, 0, rec.value_ids.ids)])))

                    update_sparepart.update({'shopware_property_ids': lst_attr})

                    for sp_rec in spare_part.shopware_property_ids:
                        if sp_rec.attribute_id.id in [attr.attribute_id.id for attr in prod.shopware_property_ids]:
                            prod_rec = [mattr for mattr in prod.shopware_property_ids if
                                        mattr.attribute_id.id == sp_rec.attribute_id.id][0]
                            pvals, cvals = set(prod_rec.value_ids.ids), set(sp_rec.value_ids.ids)
                            updateVal = list(pvals.difference(cvals))
                            if updateVal:
                                updateVal += list(cvals)
                                self.env["shopware.property.line"].browse(sp_rec.id).write(
                                    dict(value_ids=[(6, 0, updateVal)]))

                else:
                    lst_attr = []
                    for rec_attr in prod.shopware_property_ids:
                        if rec_attr.attribute_id.id in [sp_attr.id for sp_attr in spare_attr]:
                            lst_attr.append((0, 0, dict(attribute_id=rec_attr.attribute_id.id,
                                                        value_ids=[(6, 0, rec_attr.value_ids.ids)])))

                    update_sparepart.update({'shopware_property_ids': lst_attr})

                if update_sparepart:
                    spare_part.write(update_sparepart)

    def act_device_product_to_spare_parts(self, active_ids=False, context=False):
        products = self.browse(active_ids)
        self.set_on_spare_parts(products)

    @api.model
    def device_product_to_spare_parts(self, limit=1000):
        products = self.sudo().search(
            [('is_device', '=', True), ('status_on_shopware', '=', True)], limit=limit)
        self.set_on_spare_parts(products)
