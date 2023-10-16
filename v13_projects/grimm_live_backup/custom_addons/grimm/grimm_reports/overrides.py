# -*- coding: utf-8 -*-

import json

from odoo import http, _
from odoo.http import request, \
    serialize_exception as _serialize_exception
from odoo.tools import html_escape
from werkzeug.urls import url_decode
from odoo.tools.safe_eval import safe_eval
import time
from odoo.addons.web.controllers.main import ReportController
from odoo.http import content_disposition, dispatch_rpc, request, serialize_exception as _serialize_exception, Response


class GrimmReportController(ReportController):

    def translate_word(self, word):
        # TODO: Get translated word
        return word

    def invoice(self, active_model, active_ids):

        model_obj = http.request.env[active_model]
        invoice_data = model_obj.browse(active_ids[0])

        invoice_origin = invoice_data['invoice_origin'] or self.translate_word('no-origin')

        invoice_ref = invoice_data['name'] or self.translate_word('no-num')
        invoice_type = invoice_data['type']
        invoice_state = invoice_data['state']
        prepayment_order_state = invoice_data['prepayment_order_state']

        if len(active_ids) > 1:
            return _('Invoices') if invoice_type not in ['out_refund', 'in_refund'] else _('Refunds')

        if invoice_state in ['draft'] and invoice_type not in ['out_refund', 'in_refund']:
            if prepayment_order_state == 'prepayment':
                doc_name = '%s_%s' % (_('Vorkasse'), invoice_origin)
            else:
                doc_name = '%s_%s' % (_('Rechnungsentwurf'), invoice_origin)
        elif invoice_state in ['proforma', 'proforma2']:
            doc_name = '%s_%s' % (_('Vorkasse'), invoice_origin)
        elif invoice_state in ['paid', 'open', 'posted']:
            doc_name = '%s_%s' % (_('Rechnung'), invoice_ref)
        elif invoice_type in ['out_refund', 'in_refund']:
            doc_name = '%s_%s' % (_('Rechnungskorrektur'), invoice_ref)
        else:
            doc_name = '%s_%s' % (_('Missing State'), invoice_type)

        return doc_name

    def purchase(self, active_model, active_ids):

        model_obj = http.request.env[active_model]
        data = model_obj.browse(active_ids[0])

        purchase_ref = data['name'] or self.translate_word('no-num')
        purchase_type = data['state']

        if len(active_ids) > 1:
            return _('Purchase Orders') if purchase_type not in ['draft', 'sent', 'bid', 'confirmed'] else _(
                'Requests for Quotation')

        doc_name = '%s_%s' % (_('Purchase Order'), purchase_ref) if purchase_type not in [
            'draft', 'sent', 'bid', 'confirmed'] else '%s_%s' % (_('Request for Quotation'), purchase_ref)

        return doc_name

    def order(self, active_model, active_ids):

        model_obj = http.request.env[active_model]
        order_data = model_obj.browse(active_ids[0])

        if len(active_ids) > 1:
            return _('Quotes') if order_data['state'] in ['draft', 'sent', 'cancel'] else _('Orders')

        so_ref = order_data['name'] or self.translate_word('no-num')

        doc_name = '%s_%s' % (_('Order'), so_ref) if order_data['state'] not in [
            'draft', 'sent', 'cancel'] else '%s_%s' % (_('Quote'), so_ref)

        return doc_name

    def delivery(self, active_model, active_ids):

        model_obj = http.request.env[active_model]

        delivery_data = model_obj.browse(active_ids[0])

        if len(active_ids) > 1:
            # if self.base_report_name=='sponsors.picking' else self.translate_word('Picklists')
            return _('Deliveries')

        do_ref = delivery_data['name'] or self.translate_word('no-num')

        # if self.base_report_name=='sponsors.picking' else '%s_%s'
        # %(self.translate_word('Picklist'), do_ref)
        doc_name = '%s_%s' % (_('Delivery'), do_ref)

        return doc_name

    def followup(self, active_model, active_ids):

        model_obj = http.request.env[active_model]

        followup_data = model_obj.browse(active_ids[0])

        do_ref = followup_data['name'] or self.translate_word('no-num')

        # if self.base_report_name=='sponsors.picking' else '%s_%s'
        # %(self.translate_word('Picklist'), do_ref)
        doc_name = '%s_%s' % (_('Followup'), do_ref)

        return doc_name

    def generate_document_name(self, active_model, active_ids):

        method_name = {
            'account.move': 'invoice',
            'sale.order': 'order',
            'res.partner': 'followup',
            'stock.picking': 'delivery',
            'stock.picking.in': 'delivery',
            'stock.picking.out': 'delivery',
            'purchase.order': 'purchase'
        }

        if active_model not in method_name.keys():
            return False

        method = getattr(self, method_name[active_model])
        res = method(active_model, active_ids)

        return res

    @http.route(['/report/download'], type='http', auth="user")
    def report_download(self, data, token, context=None):
        """This function is used by 'action_manager_report.js' in order to trigger the download of
        a pdf/controller report.

        :param data: a javascript array JSON.stringified containg report internal url ([0]) and
        type [1]
        :returns: Response with a filetoken cookie and an attachment header
        """
        print("Report download is called..............................")
        requestcontent = json.loads(data)
        url, type = requestcontent[0], requestcontent[1]
        try:
            if type in ['qweb-pdf', 'qweb-text']:
                converter = 'pdf' if type == 'qweb-pdf' else 'text'
                extension = 'pdf' if type == 'qweb-pdf' else 'txt'

                pattern = '/report/pdf/' if type == 'qweb-pdf' else '/report/text/'
                reportname = url.split(pattern)[1].split('?')[0]

                docids = None
                if '/' in reportname:
                    reportname, docids = reportname.split('/')

                if docids:
                    # Generic report:
                    response = self.report_routes(reportname, docids=docids, converter=converter, context=context)
                else:
                    # Particular report:
                    data = dict(url_decode(url.split('?')[1]).items())  # decoding the args represented in JSON
                    if 'context' in data:
                        context, data_context = json.loads(context or '{}'), json.loads(data.pop('context'))
                        context = json.dumps({**context, **data_context})
                    response = self.report_routes(reportname, converter=converter, context=context, **data)

                report = request.env['ir.actions.report']._get_report_from_name(reportname)
                filename = "%s.%s" % (report.name, extension)
                purchase_report = request.env.ref('grimm_reports.grimm_service_begleitschein_report', False)
                if purchase_report and purchase_report.id == report.id:
                    return response

                if report and docids:
                    ids = [int(x) for x in docids.split(",")]
                    obj = request.env[report.model].browse(ids)
                    if not report.print_report_name and not len(obj) > 1:
                        #report_name = safe_eval(report.print_report_name, {'object': obj, 'time': time})
                        #filename = "%s.%s" % (report_name, extension)
                        filename = self.generate_document_name(report.model, ids)
                response.headers.add('Content-Disposition', content_disposition(filename))
                response.set_cookie('fileToken', token)
                return response
            else:
                return
        except Exception as e:
            se = _serialize_exception(e)
            error = {
                'code': 200,
                'message': "Odoo Server Error",
                'data': se
            }
            return request.make_response(html_escape(json.dumps(error)))
