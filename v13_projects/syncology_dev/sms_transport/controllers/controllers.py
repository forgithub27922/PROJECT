# -*- coding: utf-8 -*-
# from odoo import http


# class SmsTransport(http.Controller):
#     @http.route('/sms_transport/sms_transport/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sms_transport/sms_transport/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('sms_transport.listing', {
#             'root': '/sms_transport/sms_transport',
#             'objects': http.request.env['sms_transport.sms_transport'].search([]),
#         })

#     @http.route('/sms_transport/sms_transport/objects/<model("sms_transport.sms_transport"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sms_transport.object', {
#             'object': obj
#         })
