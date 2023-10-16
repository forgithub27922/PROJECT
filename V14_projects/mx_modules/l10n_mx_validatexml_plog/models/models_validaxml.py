# -*- coding: utf-8 -*-

import json
import logging
import base64
from lxml import etree
from lxml.objectify import fromstring
from zeep import Client
from zeep.transports import Transport
from datetime import datetime
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo.exceptions import UserError
from odoo.tools.float_utils import float_repr
from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split, email_escape_char, email_re
from odoo import models, fields, api, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError

# _logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logging.getLogger('zeep.client').setLevel(logging.DEBUG)

from zeep import Plugin

NS3 = '{http://www.sat.gob.mx/cfd/3}'
NS4 = '{http://www.sat.gob.mx/cfd/4}'

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.depends('restrict_mode_hash_table', 'state')
    def _compute_show_reset_to_draft_button(self):
        # OVERRIDE
        super()._compute_show_reset_to_draft_button()
        for move in self:
            if move.move_type == 'in_invoice' \
                and move.is_invoice(include_receipts=True) \
                and json.loads(move.invoice_payments_widget):
                move.show_reset_to_draft_button = False
                break
    # PLOG
    def action_post(self):
        for move in self:
            if move.is_purchase_document(include_receipts=True):
                if (self.user_has_groups('account.group_account_user') or self.user_has_groups('account.group_account_manager')):
                    return super(AccountMove, self).action_post()
                elif self.user_has_groups('account.group_account_invoice'):
                    if not move.ref:
                        raise ValidationError(_('No se encontro la Refencia del Proveedor\n Favor de proporcionar la Referencia del Proveedor valido'))
                    signed_edi = self._get_l10n_mx_edi_signed_edi_document()
                    if not signed_edi:
                        raise ValidationError(_('XML no encontrado. Favor de cargar un CFDI valido'))
        return super().action_post()


    def js_remove_outstanding_partial(self, partial_id):
        ''' Called by the 'payment' widget to remove a reconciled entry to the present invoice.

        :param partial_id: The id of an existing partial reconciled with the current invoice.
        '''
        self.ensure_one()
        partial = self.env['account.partial.reconcile'].browse(partial_id)
        move_id = partial.credit_move_id.move_id
        req = not self.user_has_groups('l10n_mx_validatexml_plog.group_account_move_romperconciliacion') \
            and move_id.move_type == 'in_invoice' \
            and move_id.is_invoice(include_receipts=True)
        print('---------- ', req)
        if req:
            raise ValidationError(_(u'No tiene permiso para romper conciliación'))
        return super().js_remove_outstanding_partial(partial_id=partial_id)



    @api.model
    def _get_user_fiscallockdate(self):
        lock_date = max(self.env.user.company_id.period_lock_date or date.min, self.env.user.company_id.fiscalyear_lock_date or date.min)
        return lock_date

    @api.model
    def get_mes_anterior(self):
        dt=date.today()
        primer = dt + relativedelta(months=-1)
        primer = '%s-%s-%s'%( primer.year, primer.month, '01' )
        primer = datetime.strptime( primer, '%Y-%m-%d' )
        return primer.date()

    @api.model
    def get_mes_actual(self):
        primer = date.today()
        primer = '%s-%s-%s'%( primer.year, primer.month, '01' )
        primer = datetime.strptime( primer, '%Y-%m-%d' )
        primer = primer + relativedelta(days=-1)
        return primer.date()

    def write(self, vals):
        if 'date' in vals:
            fecha = vals.get('date') if type( vals.get('date') ) != str else  datetime.strptime( vals.get('date'), '%Y-%m-%d' ).date()
            for move in self:
                try:
                    lock_date = move.company_id._get_user_fiscal_lock_date()
                    lock_date_start = '%s-%s-01'%( lock_date.year, lock_date.month )
                    lock_date_start = datetime.strptime( lock_date_start, '%Y-%m-%d' ).date()
                except:
                    lock_date_start = False
                today = fields.Date.context_today(self)
                lastmonth = move.get_mes_anterior()
                fechaXML = fields.Datetime.from_string(fecha).date()
                if move.is_purchase_document(include_receipts=True):
                    if self.user_has_groups('account.group_account_manager'):
                        if fechaXML <= lock_date:
                            invoice_date = today
                        else:            
                            invoice_date = fechaXML
                        vals['date'] = invoice_date
                        vals['invoice_date'] = invoice_date
                    elif self.user_has_groups('account.group_account_invoice'):
                        if fechaXML < lock_date:
                            invoice_date = today
                        else:            
                            invoice_date = fechaXML
                        vals['date'] = invoice_date
                        vals['invoice_date'] = invoice_date
        return super().write(vals)

    def _check_fiscalyear_lock_date(self):
        for move in self:
            try:
                lock_date = move._get_user_fiscallockdate()
                lock_date_start = '%s-%s-01'%( lock_date.year, lock_date.month )
                lock_date_start = datetime.strptime( lock_date_start, '%Y-%m-%d' ).date()
            except:
                lock_date_start = False
            lastmonth = move.get_mes_anterior()
            fechaXML = move.date
            if (self.user_has_groups('account.group_account_user') or self.user_has_groups('account.group_account_manager')):
                return True
            elif self.user_has_groups('account.group_account_invoice'):
                if lastmonth > fechaXML:
                    raise UserError("Solo se permite cargar facturas del Mes Anterior")
                return True
        return super(AccountMove, self)._check_fiscalyear_lock_date()

class AccountInvoiceCfdiUpload(models.TransientModel):
    _inherit = 'account.invoice.cfdiupload'

    def validaxml_extrainfo(self, invoice_id, tree, vals):
        res = super(AccountInvoiceCfdiUpload, self).validaxml_extrainfo(invoice_id, tree, vals)
        fecha = tree.get('Fecha', '').split('T')
        try:
            lock_date = invoice_id._get_user_fiscallockdate()
            lock_date_start = '%s-%s-01'%( lock_date.year, lock_date.month )
            lock_date_start = datetime.strptime( lock_date_start, '%Y-%m-%d' ).date()
        except:
            lock_date_start = False
        lastmonth = invoice_id.get_mes_anterior()
        today = fields.Date.context_today(self)
        today_sp = ('%s'%today).split('-')
        firstDayMonth = fields.Datetime.from_string('%s-%s-01'%( today_sp[0], today_sp[1] )).date()
        invoice_date = fecha and fecha[0] or ''
        fechaXML = fields.Datetime.from_string(invoice_date).date()
        if (self.user_has_groups('account.group_account_user') or self.user_has_groups('account.group_account_manager')):
            if fechaXML <= lock_date:
                invoice_date = today
            else:            
                invoice_date = fechaXML
        elif self.user_has_groups('account.group_account_invoice'):
            logging.info('------ fechaXML %s - lock_date %s - hoy %s - lastmonth %s - firstDayMonth %s ' %( fechaXML, lock_date, today, lastmonth, firstDayMonth ) )
            if lastmonth > fechaXML:
                raise UserError("No se permite cargar facturas del Mes Anterior")
            if firstDayMonth > fechaXML:
                if lock_date > fechaXML:
                    raise UserError("No se permite cargar facturas del Mes Anterior")
            if fechaXML < lock_date:
                invoice_date = today
            else:            
                invoice_date = fechaXML
        res['invoice_date'] = invoice_date
        return res




