import urllib
import logging
import collections
import email

import werkzeug

from odoo import _, http
from odoo.http import request, Response
from odoo.tools import config, pycompat

import requests

_logger = logging.getLogger(__name__)


def get_route(url):
    url_parts = url.split('?')
    path = url_parts[0]
    query_string = url_parts[1] if len(url_parts) > 1 else None
    # router = request.httprequest.app.get_db_router(request.db).bind('')
    router = http.root.get_db_router(request.db).bind('')
    match = router.match(path, query_args=query_string)
    method = router.match(path, query_args=query_string)[0]
    params = dict(urllib.parse.parse_qsl(query_string))
    if len(match) > 1:
        params.update(match[1])
    return method, params, path


def make_error_response(status, message):
    exception = werkzeug.exceptions.HTTPException()
    exception.code = status
    exception.description = message
    return exception


def get_response(url):
    _logger.info(url)
    if not bool(urllib.parse.urlparse(url).netloc):
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        method, params, path = get_route(url)
        params.update({'csrf_token': request.csrf_token()})
        session = requests.Session()
        session.cookies['session_id'] = request.session.sid
        try:
            response = session.post("%s%s" % (base_url, path), params=params, verify=False)
            return response.status_code, response.headers, response.content
        except:
            _logger.info("Trying custom certificate")
            custom_cert = config.get("muk_custom_certificate", False)
            try:
                _logger.info("Using Certificate: {}".format(custom_cert))
                response = session.post("%s%s" % (base_url, path), params=params, verify=custom_cert)
                return response.status_code, response.headers, response.reason
            except:
                try:
                    _logger.info("Custom Certificate didn't work")
                    response = session.post("%s%s" % (base_url, path), params=params, verify=False)
                    return response.status_code, response.headers, response.reason
                except Exception as e:
                    _logger.exception("Request failed!")
                    return 501, [], str(e)
    else:
        try:
            response = requests.get(url)
            return response.status_code, response.headers, response.content
        except requests.exceptions.RequestException as exception:
            try:
                return exception.response.status_code, exception.response.headers, exception.response.reason
            except Exception as e:
                _logger.exception("Request failed!")
                return 501, [], str(e)


class MailParserController(http.Controller):
    
    _Attachment = collections.namedtuple('Attachment', 'name mimetype extension url info')
    
    @http.route('/web/preview/mail', auth="user", type='json')
    def preview_mail(self, url, attachment=None, **kw):
        status, headers, content = get_response(url)
        if status != 200:
            return make_error_response(status, content or _("Unknown Error"))
        elif headers['content-type'] != 'message/rfc822':
            return werkzeug.exceptions.UnsupportedMediaType(
                _("Unparsable message! The file has to be of type: message/rfc822"))
        else:
            if not attachment:
                content = content.decode("latin-1").encode("utf8")
            try:
                message = request.env['mail.thread'].message_parse(content, False)
            except:
                message = pycompat.to_text(content)
                message = email.message_from_string(message)
                message = request.env['mail.thread'].message_parse(message, False)
            return message
