# -*- coding: utf-8 -*-

import werkzeug.wrappers
import logging
import json
import odoo
import odoo.modules.registry
from odoo import registry as registry_get
from odoo.addons.web.controllers.main import ensure_db
from odoo.tools import html_escape, pycompat, ustr, apply_inheritance_specs, lazy_property, float_repr, osutil
from odoo.http import content_disposition, dispatch_rpc, request, serialize_exception as _serialize_exception
from odoo.tools.translate import _
from odoo import http
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

CONTENT_MAXAGE = http.STATIC_CACHE_LONG  # menus, translations, static qweb
DBNAME_PATTERN = '^[a-zA-Z0-9][a-zA-Z0-9_.-]+$'
COMMENT_PATTERN = r'Modified by [\s\w\-.]+ from [\s\w\-.]+'

def validresponse(data, status=200):
    return werkzeug.wrappers.Response(
        status=status, content_type="application/json; charset=utf-8", response=json.dumps(data),
    )

class PosWsYeidala(http.Controller):

    def returnResponse(self, values):
        body = json.dumps(values, default=ustr)
        response = request.make_response(body, [
            ('Content-Type', 'application/json'),
            ('Cache-Control', 'public, max-age=' + str(CONTENT_MAXAGE)),
        ])
        request.session.logout(keep_db=True)
        return response

    def action_authenticate(self, login='', password=''):
        values =  {}
        try:
            uid = request.session.authenticate(request.session.db, login, password)
            return {'uid': uid}
        except odoo.exceptions.AccessDenied as e:
            if e.args == odoo.exceptions.AccessDenied().args:
                values['error'] = _("Wrong login/password")
            else:
                values['error'] = e.args[0]
        return values        

    @http.route('/web/refund', type='http', auth="none", csrf=False)
    def refund(self, login=None, password=None, *kw):
        ensure_db()
        data = dict( request.params )
        values =  {}
        ws_nationalsoft = request.env['pos.order.nationalsoft'].sudo()
        values = ws_nationalsoft.action_process_refund(data)
        return self.returnResponse(values)
        

    @http.route('/web/posorder', type='http', auth="none", methods=['POST', 'OPTIONS', 'GET'], csrf=False, cors="*")
    def posorder(self, *kw):
        print("KEWWWWWWWWWWWWWWWWW",kw)
        # ensure_db()
        # raw_body = http.request.httprequest.data or "{}"
        # json_datas = json.loads( raw_body)
        # ws_nationalsoft = request.env['pos.order.nationalsoft'].sudo()
        # print("\n\nREQ::::>>>>>>", request.params)
        # values = ws_nationalsoft.action_process_posns(json_datas, request.params['login'])
        return False


# odoo.pos
# http://192.168.100.55:8098/web/posorder
# {'login': 'PosNS@Plog.com', 'password': 'IntPosNSOdoo22', 'IdEmpresa': 'Apodaca', 'NumeroOrden': '110020', 'TipoCancelacion': 'devolucion'}