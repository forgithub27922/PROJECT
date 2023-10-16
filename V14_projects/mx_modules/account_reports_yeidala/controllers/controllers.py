# -*- coding: utf-8 -*-
# from odoo import http


# class AccountReportsYeidala(http.Controller):
#     @http.route('/account_reports_yeidala/account_reports_yeidala/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/account_reports_yeidala/account_reports_yeidala/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('account_reports_yeidala.listing', {
#             'root': '/account_reports_yeidala/account_reports_yeidala',
#             'objects': http.request.env['account_reports_yeidala.account_reports_yeidala'].search([]),
#         })

#     @http.route('/account_reports_yeidala/account_reports_yeidala/objects/<model("account_reports_yeidala.account_reports_yeidala"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('account_reports_yeidala.object', {
#             'object': obj
#         })
