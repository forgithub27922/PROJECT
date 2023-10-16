# -*- coding: utf-8 -*-

import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.http import content_disposition, dispatch_rpc, request, \
                      serialize_exception as _serialize_exception
from odoo.addons.web.controllers.main import serialize_exception,content_disposition
from odoo import api, fields, models, _

import os
import glob
import zipfile
import shutil
try:
    from StringIO import StringIO ## for Python 2
except ImportError:
    from io import StringIO ## for Python 3

import odoo
import odoo.modules.registry
from odoo import http


class LayoutPaymentBatchBanregio(http.Controller):
    TYPES_MAPPING = {
        'doc': 'application/vnd.ms-word',
        'html': 'text/html',
        'odt': 'application/vnd.oasis.opendocument.text',
        'pdf': 'application/pdf',
        'sxw': 'application/vnd.sun.xml.writer',
        'xls': 'application/vnd.ms-excel',
        'zip': 'application/zip'
    }

    @http.route('/web/report_layoutpaymentbatchbanregio', type='http', auth="public")
    @serialize_exception
    def index(self, **kw):
        move_ids = eval(kw.get('ids'))
        data = request.env['account.move'].browse(move_ids).action_layout_payment_batch_banregio_datas()
        content_type = ('Content-Type', 'application/vnd.ms-excel')
        disposition_content = ('Content-Disposition', content_disposition(data.get('filename')))
        return request.make_response(
            data.get('file'), [content_type, disposition_content])




