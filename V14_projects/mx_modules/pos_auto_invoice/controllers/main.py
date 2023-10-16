# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import werkzeug.urls
import json
from odoo import http
from odoo.addons.http_routing.models.ir_http import unslug, slug
from odoo.addons.website.models.ir_http import sitemap_qs2dom
from odoo.tools import html_escape, pycompat, ustr, apply_inheritance_specs, lazy_property, float_repr, osutil
from odoo.http import content_disposition, dispatch_rpc, request, serialize_exception as _serialize_exception
from odoo.tools.translate import _
from odoo.http import request
from odoo import api, fields
from odoo import fields, http, SUPERUSER_ID, tools, _

CONTENT_MAXAGE = http.STATIC_CACHE_LONG  # menus, translations, static qweb
DBNAME_PATTERN = '^[a-zA-Z0-9][a-zA-Z0-9_.-]+$'
COMMENT_PATTERN = r'Modified by [\s\w\-.]+ from [\s\w\-.]+'


usages = [
    ('G01', _('[G01] Adquisición de mercancías')),
    ('G02', _('[G02] Devoluciones, descuentos o bonificaciones')),
    ('G03', _('[G03] Gastos en general')),
    ('I01', _('[I01] Construcciones')),
    ('I02', _('[I02] Mobilario y equipo de oficina por inversiones')),
    ('I03', _('[I03] Equipo de transporte')),
    ('I04', _('[I04] Equipo de cómputo y accesorios')),
    ('I05', _('[I05] Dados, troqueles, moldes, matrices y herramental')),
    ('I06', _('[I06] Comunicaciones telefónicas')),
    ('I07', _('[I07] Comunicaciones satelitales')),
    ('I08', _('[I08] Otra maquinaria y equipo')),
    ('D01', _('[D01] Honorarios médicos, dentales y gastos hospitalarios.')),
    ('D02', _('[D02] Gastos médicos por incapacidad o discapacidad')),
    ('D03', _('[D03] Gastos funerales')),
    ('D04', _('[D04] Donativos')),
    ('D05', _('[D05] Intereses reales efectivamente pagados por créditos hipotecarios (casa habitación)')),
    ('D06', _('[D06] Aportaciones voluntarias al SAR')),
    ('D07', _('[D07] Primas por seguros de gastos médicos')),
    ('D08', _('[D08] Gastos de transportación escolar obligatoria')),
    ('D09', _('[D09] Depósitos en cuentas para el ahorro, primas que tengan como base planes de pensiones.')),
    ('D10', _('[D10] Pagos por servicios educativos (colegiaturas)')),
    ('P01', _('[P01] Por definir')),
]

class WebsitePosAutoInvoice(http.Controller):

    def returnResponse(self, values):
        body = json.dumps(values, default=ustr)
        response = request.make_response(body, [
            ('Content-Type', 'application/json'),
            ('Cache-Control', 'public, max-age=' + str(CONTENT_MAXAGE)),
        ])
        return response

    @http.route([
        '/cfdi/validate/<page>',
    ], type='http', auth="none", csrf=False)
    def cfdivalidate(self, page=None, **post):
        ConfigModel = request.env['pos.config'].with_user(SUPERUSER_ID)
        PosModel = request.env['pos.order'].with_user(SUPERUSER_ID)
        OrderModel = request.env['pos.order'].with_user(SUPERUSER_ID)
        PartnerModel = request.env['res.partner'].with_user(SUPERUSER_ID)

        if page and page == 'tickets':
            sucursal = 'sucursal_id' in post and post['sucursal_id'] != '' and ConfigModel.browse(int(post['sucursal_id']))
            notickets = '%s_%s'%( sucursal.empresans_id, post.get('notickets'))
            order_id = OrderModel.search([('session_id.config_id', '=', sucursal.id), ('noorderns', '=', notickets)])
            if not order_id:
                return self.returnResponse({'error': 'No se encuentra el numero de venta'})
            else:
                return self.returnResponse({'ok': order_id.id})
        if page and page == 'rfc':
            vat = post.get('vat', '').upper()
            vals = { 'vat': '', 'name': '', 'zip': '', 'email': '', 'partner_id': 0}
            partner_id = PartnerModel.search([('vat', '=', vat)])
            if partner_id:
                vals = { 'vat': partner_id.vat, 'name': partner_id.name, 'zip': partner_id.zip, 'email': partner_id.email, 'partner_id': partner_id.id, 'usocfdi': partner_id.l10n_mx_edi_usage or 'G03'}
            return self.returnResponse(vals)
        if page and page == 'facturas':
            vat = post.get('vat', '').upper()
            company_id = request.env.ref('__export__.res_company_12_276637f1', raise_if_not_found=False).sudo()
            user_id = company_id.partner_id.user_ids
            sucursal = 'sucursal_id' in post and post['sucursal_id'] != '' and ConfigModel.browse(int(post['sucursal_id']))
            notickets = '%s_%s'%( sucursal.empresans_id, post.get('notickets'))
            order_id = OrderModel.with_company(company_id).browse(int(post['order_id']))
            partner_id = PartnerModel.search([('vat', '=', vat)])
            if not partner_id:
                payment_method_id = request.env['l10n_mx_edi.payment.method'].search([('code', '=', '99')], limit=1)
                payment_term_id = request.env.ref('account.account_payment_term_immediate', raise_if_not_found=False)
                vals = {
                    'name': post.get('name'),
                    'vat': vat,
                    'zip': post.get('zip'),
                    'email': post.get('email') or '',
                    'type': 'contact',
                    'l10n_mx_edi_usage': post.get('usocfdi'),
                    'l10n_mx_edi_payment_policy': 'PUE',                    
                    'l10n_mx_edi_payment_method_id': payment_method_id and payment_method_id.id or False,
                    'property_payment_term_id': payment_term_id and payment_term_id.id or False,
                    'country_id': company_id.country_id and company_id.country_id.id or False,
                    'company_id': company_id.id,
                    'active': True,
                    'is_company': True,
                    'customer_rank': 1,
                }
                partner_id = PartnerModel.with_company(company_id).create(vals)
                request.env.cr.commit()
            else:
                vals = {
                    'email': post.get('email') or '',
                    'l10n_mx_edi_usage': post.get('usocfdi'),
                    'zip': post.get('zip'),
                    'name': post.get('name'),
                }
                partner_id.write(vals)
                request.env.cr.commit()
            res_val = order_id.action_auto_invoice(partner_id=partner_id)
            if 'inv_id' in res_val:
                inv_id = res_val.get('inv_id')
                if inv_id.l10n_mx_edi_cfdi_uuid:
                    return self.returnResponse({'ok': order_id.id})
        return self.returnResponse({'error':'Error en el proceso'})

    @http.route([
        '/cfdi',
        '/cfdi/page/<page>',
        '/cfdi/page/<page>/<idorder>',        
    ], type='http', methods=['GET', 'POST'], auth="public", website=True, sitemap=False)
    def cfdi(self, page=None, idorder=None, **post):
        values, errors = {}, {}
        PosModel = request.env['pos.order'].sudo()
        PartnerModel = request.env['res.partner'].sudo()
        ConfigModel = request.env['pos.config'].sudo()
        OrderModel = request.env['pos.order'].sudo()
        InvoiceModel = request.env['account.move'].sudo()
        company_id = request.env.ref('__export__.res_company_12_276637f1', raise_if_not_found=False)
        error_message = []
        nombresucursal = 'sucursal' in post and post['sucursal'] != '' and ConfigModel.search([('empresans_id', '=', post['sucursal'])], limit=1)
        sucursal = 'sucursal_id' in post and post['sucursal_id'] != '' and ConfigModel.browse(int(post['sucursal_id']))
        values["sucursales"] = ConfigModel.search([('company_id', '=', company_id.id)])
        values["sucursal"] = sucursal or nombresucursal or ''
        if not page:
            values.update({
                'error': errors,
                'checkout': post,
            })
            return request.render("pos_auto_invoice.index", values)
        if page == 'order' and idorder != None:
            order_id = OrderModel.browse( int(idorder) )
            order_id.action_receipt_to_customer_auto()
            post.update({
                'order_id': order_id.id,
                'email': order_id.partner_id.email
            })            
            values.update({
                'error': 'La factura ya fue procesada y enviada al correo de contacto que se proporciono',
                'checkout': post,
            })
            return request.render("pos_auto_invoice.noencontrado", values)            

        if page == 'rfc':
            notickets = '%s_%s'%( sucursal.empresans_id, post.get('notickets'))
            order_id = OrderModel.search([('session_id.config_id', '=', sucursal.id), ('noorderns', '=', notickets)])
            post.update({
                'order_id': order_id.id,
                'email': order_id.partner_id.email or '',
                'usocfdi': order_id.partner_id.email or ''
            })
            if order_id.is_invoiced and order_id.account_move:
                values.update({
                    'error': 'La factura ya fue procesada y enviada al correo de contacto que se proporciono "%s" '%( order_id.partner_id.email ) ,
                    'checkout': post,
                })
                return request.render("pos_auto_invoice.noencontrado", values)
                inv_datas = order_id.action_pos_order_invoice()
                if 'res_id' in inv_datas:
                    inv_id = InvoiceModel.browse( inv_datas['res_id'] )
                    if inv_id.l10n_mx_edi_cfdi_uuid:
                        return request.render("pos_auto_invoice.email", values)
            values['order_id'] = order_id.id
            values.update({
                'error': errors,
                'post': post,
                'checkout': post,
                'notickets': post.get('notickets') or '',
                'order': order_id,
                'sucursal_id': sucursal.id,
                'partner_id': order_id.partner_id and order_id.partner_id.id or 0,
                'usos': usages,
                'uso': post.get('uso')
            })            
            return request.render("pos_auto_invoice.rfc", values)
        if page == 'factura':
            vat = post.get('vat', '').upper()
            order_ids = OrderModel.browse( int(post.get('order_id', '0')) )
            partner_id = PartnerModel.search([('vat', '=', vat)])
            if not partner_id:
                payment_method_id = request.env['l10n_mx_edi.payment.method'].search([('code', '=', '99')], limit=1)
                payment_term_id = request.env.ref('account.account_payment_term_immediate', raise_if_not_found=False)
                vals = {
                    'name': post.get('name'),
                    'vat': vat,
                    'zip': post.get('zip'),
                    'email': post.get('email'),
                    'type': 'contact',
                    'l10n_mx_edi_usage': 'G03',
                    'l10n_mx_edi_payment_method_id': payment_method_id and payment_method_id.id or False,
                    'l10n_mx_edi_payment_policy': 'PUE',
                    'property_payment_term_id': payment_term_id and payment_term_id.id or False,
                    'country_id': company_id.country_id and company_id.country_id.id or False,
                    'company_id': company_id.id,
                    'active': True,
                    'is_company': True,
                    'customer_rank': 1,
                }
                partner_id = PartnerModel.create(vals)
                request.env.cr.commit()
            for order_id in order_ids:
                res_val = order_id.action_auto_invoice(partner_id=partner_id)
                if 'inv_id' in res_val:
                    inv_id = res_val.get('inv_id')
                    if inv_id.l10n_mx_edi_cfdi_uuid:
                        return request.render("pos_auto_invoice.email", values)
        if page == 'email':
            return request.render("pos_auto_invoice.email", values)
        return request.render("pos_auto_invoice.noencontrado", values)