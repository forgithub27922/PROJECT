# -*- coding: utf-8 -*-
# from odoo import http


# class SmsCore(http.Controller):
#     @http.route('/sms_core/sms_core/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sms_core/sms_core/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('sms_core.listing', {
#             'root': '/sms_core/sms_core',
#             'objects': http.request.env['sms_core.sms_core'].search([]),
#         })

#     @http.route('/sms_core/sms_core/objects/<model("sms_core.sms_core"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sms_core.object', {
#             'object': obj
#         })
