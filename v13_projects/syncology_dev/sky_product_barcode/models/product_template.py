##########################################################################################
#
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#    Copyright (C) 2020 Skyscend Business Solutions Pvt. Ltd. (http://www.skyscendbs.com)
#
##########################################################################################
from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
import json


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def find_product_by_ref_using_barcode(self, barcode):
        product = self.search([('barcode', '=', barcode)], limit=1)

        if not product:
            action = self.env.ref('sky_product_barcode.action_product_barcode_wizard')
            result = action.read()[0]
            context = safe_eval(result['context'])
            context.update(
                {'default_state': 'warning',
                 'default_status': _('Product with Barcode %s is not existing!') % barcode,
                 }
            )
            result['context'] = json.dumps(context)
            return result
        action = self.env.ref('stock.product_template_action_product')
        result = action.read()[0]
        res = self.env.ref('product.product_template_only_form_view', False)
        result['views'] = [(res and res.id or False, "form")]
        result['res_id'] = product.id
        return result
