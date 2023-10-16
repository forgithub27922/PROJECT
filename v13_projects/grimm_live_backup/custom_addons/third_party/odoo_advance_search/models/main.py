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


class GrimmAdvanceSearchController(ReportController):
    @http.route(['/grimm/advance_search/call_kw/<path:path>'], type='json', auth="user")
    def advance_search_method(self, model, method, args, kwargs, path=None):
        model_instance = request.env[model].name_search(args[0], operator='ilike')
        return_instance = []
        allowed_companies = args[1].get("allowed_company_ids", [])
        try:
            if allowed_companies:
                for k in model_instance:
                    obj = request.env[model].browse(k[0])
                    company_id = getattr(obj, "company_id", False)
                    if company_id:
                        if company_id.id in allowed_companies:
                            return_instance.append(k)
                    else:
                        return_instance.append(k)
            else:
                return_instance = model_instance
            return return_instance
        except:
            return model_instance