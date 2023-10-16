# -*- coding: utf-8 -*-


from odoo import models, fields


class ProductAttributeSet(models.Model):
    _name = 'product.attribute.set'
    _description = 'Product Attribute Set'

    name = fields.Char('Name', required=True)
    description = fields.Char('Description')
    product_attribute_ids = fields.Many2many(comodel_name='product.attribute',
                                             relation='product_attr_set_product_attr_rel', column1='attr_set_id',
                                             column2='attr_id')

    def write(self, vals):
        '''
        Inherited for task OD-1372 (Delete Attributes from Products)
        :param vals:
        :return:
        '''
        result = super(ProductAttributeSet, self).write(vals)
        if isinstance(vals, dict) and vals.get("product_attribute_ids", False):
            attr_ids = self.mapped("product_attribute_ids.id")
            attr_ids.append(0)
            set_ids = self.ids
            set_ids.append(0)
            self._cr.execute("SELECT DISTINCT(ID) FROM shopware6_product_product WHERE openerp_id IN (SELECT DISTINCT(product_tmpl_id)  FROM product_template_specifications WHERE attr_id NOT IN %s AND product_tmpl_id IN (SELECT id FROM product_product WHERE attribute_set_id IN %s))" % (str(tuple(attr_ids)), str(tuple(set_ids))))
            shopware_prod_ids = [x[0] for x in self._cr.fetchall()]
            # Deleting product template specification.
            self._cr.execute("DELETE FROM product_template_specifications WHERE attr_id NOT IN %s AND product_tmpl_id IN (SELECT id FROM product_product WHERE attribute_set_id IN %s)" % (
                str(tuple(attr_ids)), str(tuple(set_ids))))

            prod_template = self.env["product.template"]
            for s_id in shopware_prod_ids:
                calling = prod_template.export_with_delay_record(model='shopware6.product.product',rec_id=s_id,fields= ["technical_specifications"],priority=15)
        return result
