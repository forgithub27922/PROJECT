# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError

from odoo.addons.mail.models.mail_template import format_date, mako_safe_template_env, mako_template_env
from odoo.tools import format_amount, format_datetime

_logger = logging.getLogger(__name__)


class GrimmPretextTemplate(models.Model):
    _name = 'grimm.pretext.template'
    _description = 'Grimm Pre-Text Template'
    _order = 'name'

    name = fields.Char('Name', required=True, copy=False)
    model_id = fields.Many2one(string='Model', comodel_name='ir.model', copy=True)
    text = fields.Html('Text', required=True, copy=True)

    @api.model
    def default_get(self, fields_list):
        res = super(GrimmPretextTemplate, self).default_get(fields_list)
        default_model_id = self._context.get('default_model_id', False)
        if default_model_id:
            default_model = self.env['ir.model'].search([('model', '=', default_model_id)])
            if default_model:
                res.update({'model_id': default_model.id})
        return res

    @api.model
    def render_template(self, template_txt, record):
        res = self._render_template(template_txt, record)
        return res

    @api.model
    def _render_template(self, template_txt, record):
        result = ""

        # try to load the template
        try:
            mako_env = mako_safe_template_env if self.env.context.get('safe') else mako_template_env
            template = mako_env.from_string(tools.ustr(template_txt))
        except Exception:
            _logger.info("Failed to load template %r", template_txt, exc_info=True)
            return template_txt or result

        variables = dict(
            format_date=lambda date, format=False, context=self._context: format_date(self.env, date, format),
            format_tz=lambda dt, tz=False, format=False, context=self._context: format_datetime(self.env, dt, tz, format),
            format_amount=lambda amount, currency, context=self._context: format_amount(self.env, amount, currency),
            user=self.env.user,
            ctx=self._context,  # context kw would clash with mako internals
        )

        variables['object'] = record
        try:
            render_result = template.render(variables)
        except Exception:
            _logger.info("Failed to render template %r using values %r" % (template, variables), exc_info=True)
            raise UserError(_("Failed to render template %r using values %r") % (template, variables))
        if render_result == u"False":
            render_result = u""
        result = render_result

        return result
