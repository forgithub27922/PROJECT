# -*- coding: utf-8 -*-
#############################################################
#   No need for this controller so disabled in init hook.   #
#############################################################
import odoo
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import Home
from odoo.addons.web.controllers.main import ensure_db
from odoo import _
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class LoginPwdController(Home):

    @http.route(csrf=False)
    def web_login(self, redirect=None, **kw):
        ensure_db()
        request.params['login_success'], expired = False, False
        if request.httprequest.method == 'GET' and redirect and request.session.uid:
            return http.redirect_with_hash(redirect)

        if not request.uid:
            request.uid = odoo.SUPERUSER_ID

        values = request.params.copy()
        try:
            values['databases'] = http.db_list()
        except odoo.exceptions.AccessDenied:
            values['databases'] = None

        if request.httprequest.method == 'POST':
            old_uid = request.uid
            try:
                uid = request.session.authenticate(request.session.db, request.params['login'], request.params['password'])
                expired = True if uid and request.env.user._password_has_expired() else False
                if expired:
                    raise odoo.exceptions.AccessError(_("Password expired. Please contact the administrator!"))
                request.params['login_success'] = True
                user = request.env.user
                pwd_exp_days = request.env['res.company'].browse(user.company_id.id).password_expiration
                days_diff = datetime.now() - datetime.strptime(str(user.password_write_date),
                                                               '%Y-%m-%d %H:%M:%S')
                limit = pwd_exp_days - days_diff.days
                # if limit in range(0, 4):
                #     request.env.user.notify_warning(_(
                #         "Dear %s, your password expires in %d day(s). Please change your password." % (
                #             request.env.user.name, limit)), _("Password Expiry Notice!"), True)
                return http.redirect_with_hash(self._login_redirect(uid, redirect=redirect))
            except odoo.exceptions.AccessDenied as e:
                request.uid = old_uid
                if e.args == odoo.exceptions.AccessDenied().args:
                    values['error'] = _("Wrong login/password")
                else:
                    values['error'] = e.args[0]
            except odoo.exceptions.AccessError as e:
                request.uid = old_uid
                values['error'] = _("Password expired. Please contact the administrator!")
        else:
            if 'error' in request.params and request.params.get('error') == 'access':
                values['error'] = _('Only employee can access this database. Please contact the administrator.')

        if 'login' not in values and request.session.get('auth_login'):
            values['login'] = request.session.get('auth_login')

        if not odoo.tools.config['list_db']:
            values['disable_database_manager'] = True

        response = request.render('web.login', values)
        response.headers['X-Frame-Options'] = 'DENY'
        return response
