from odoo import http, _
from odoo.http import request
from odoo.addons.stock_barcode.controllers.main import StockBarcodeController
from odoo import models, fields, api, tools
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class StockBarcodeController(StockBarcodeController):

    @http.route('/stock_barcode/scan_from_main_menu', type='json', auth='user')
    def main_menu(self, barcode, **kw):
        """ Receive a barcode scanned from the main menu and return the appropriate
            action (open an existing / new picking) or warning.
        """
        ret_open_picking = self.try_open_picking(barcode)
        if ret_open_picking:
            return ret_open_picking

        if request.env.user.has_group('stock.group_stock_multi_locations'):
            ret_new_internal_picking = self.try_new_internal_picking(barcode)
            if ret_new_internal_picking:
                return ret_new_internal_picking
        if barcode == "GRIMM.PHOTO_SCAN":
            photo_window = self.try_open_photo_scan(barcode)
            return photo_window if photo_window else False
        if barcode == "GRIMM.INTERNAL_TRANSFER":
            internal_transfer_window = self.try_open_internal_transfer(barcode)
            return internal_transfer_window if internal_transfer_window else False

        if request.env.user.has_group('stock.group_stock_multi_locations'):
            return {'warning': _('No picking or location corresponding to barcode %(barcode)s') % {'barcode': barcode}}
        else:
            return {'warning': _('No picking corresponding to barcode %(barcode)s') % {'barcode': barcode}}

    @http.route('/stock_barcode/scan_from_photo_main_menu', type='json', auth='user')
    def photo_main_menu(self, barcode, **kw):
        """ Here we handle all product scan for photo scan. If we found product then will update is_photo_done field of product.
            If scan code is for return main menu then return user to Barcode main menu.
        """
        if barcode == "O-CMD.MAIN-MENU":
            action = request.env.ref('stock_barcode.stock_barcode_action_main_menu').read()[0]
            return {'action': action} if action else False
        product = request.env['product.product'].sudo().search(['|', ('barcode', '=', barcode), ('default_code', '=', barcode)], limit=1)
        if product:
            if product.is_photo_done:
                raise UserError(_("Photo has been already taken for %s." % (barcode)))
            is_update = product.sudo().write({'is_photo_done': True, 'photo_date':fields.Datetime.now()})
            return {'notify': _('Photo entry has been updated for <b>%(barcode)s</b> <br/> %(name)s') % {'barcode': barcode, 'name': product.name}}
        else:
            return {'warning': _('No Product corresponding to barcode %(barcode)s') % {'barcode': barcode}}

    def try_open_photo_scan(self, barcode):
        """ If barcode represents a picking, open it
        """
        action = request.env.ref('grimm_barcode_scan.photo_barcode_action_main_menu').read()[0]
        return {'action': action} if action else False

    @http.route('/stock_barcode/scan_from_transfer_main_menu', type='json', auth='user')
    def scan_from_transfer_main_menu(self, barcode, **kw):
        """ Receive a barcode scanned for internal transfer.
        """
        if barcode == "O-CMD.MAIN-MENU":
            action = request.env.ref('stock_barcode.stock_barcode_action_main_menu').read()[0]
            return {'action': action} if action else False
        if barcode == "GRIMM.INTERNAL_TRANSFER":
            internal_transfer_window = self.try_open_internal_transfer(barcode)
            return internal_transfer_window if internal_transfer_window else False

        stock_picking = request.env['stock.picking'].sudo().search(
            [('picking_type_id.code', '=', 'internal'), ('state', '=', 'assigned'), '|', ('move_line_ids.product_id.barcode', '=', barcode), ('move_line_ids.product_id.default_code', '=', barcode)])
        if not stock_picking:
            return {'warning': _('No Internal Transfer in Ready state for corresponding product barcode %(barcode)s') % {'barcode': barcode}}
        action = request.env.ref('grimm_barcode_scan.grimm_stock_picking_action_kanban').read()[0]
        action["domain"] = [('id', 'in', stock_picking.ids)]
        if len(stock_picking.ids) == 1:
            action = request.env.ref('stock_barcode.stock_picking_action_form').read()[0]
            action["res_id"] = stock_picking.ids[0]
        action["context"] = {'force_detailed_view': True}
        return {'action': action} if action else False

    def try_open_internal_transfer(self, barcode):
        """ Open main menu for Internal transfer.
        """
        action = request.env.ref('grimm_barcode_scan.internal_transfer_action_main_menu').read()[0]
        return {'action': action} if action else False