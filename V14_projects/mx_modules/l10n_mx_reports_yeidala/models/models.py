# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from __future__ import division

from contextlib import contextmanager
import locale
import re
import json
import logging
from unicodedata import normalize
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, float_compare, translate

_logger = logging.getLogger(__name__)


class MxReportPartnerLedgerYeidala(models.AbstractModel):
    _name = "l10n_mx.account.diot.yeidala"
    _inherit = "l10n_mx.account.diot"
    _description = "DIOT - Yeidala"

    filter_date = {'mode': 'range', 'filter': 'this_month'}
    filter_all_entries = None

    def _get_columns_name(self, options):
        return [
            {},
            {'name': _('Type of Third')},
            {'name': _('Type of Operation')},
            {'name': _('VAT')},
            {'name': _('Country')},
            {'name': _('Importe')},
            {'name': _('Paid 16%'), 'class': 'number'},
            {'name': _('Paid 16% - Non-Creditable'), 'class': 'number'},
            {'name': _('Paid 8 %'), 'class': 'number'},
            {'name': _('Paid 8 % - Non-Creditable'), 'class': 'number'},
            {'name': _('Importation 16%'), 'class': 'number'},
            {'name': _('Paid 0%'), 'class': 'number'},
            {'name': _('Exempt'), 'class': 'number'},
            {'name': _('Withheld'), 'class': 'number'},
        ]


    # dataResult  {14: {'total': 3000.0}}
    # ----partners  {res.partner(14,): {3: 500.0, 4: 500.0, 7: 500.0, 9: 500.0, 10: 500.0, 11: 500.0, 'lines': account.move.line(45, 26, 62, 36, 52, 78)}}

    @api.model
    def _get_lines(self, options, line_id=None):
        if line_id:
            line_id = line_id.replace('partner_', '')
        lines = super(MxReportPartnerLedgerYeidala, self)._get_lines(options=options, line_id=line_id)
        dataResult = {}
        resultGroupByPartner = self._group_by_partner_id(options=options, line_id=line_id)
        resultGroupByAccount = self._do_query_group_by_account(options=options, line_id=line_id)

        sorted_partners = sorted(resultGroupByPartner, key=lambda p: p.name or '')
        for res in resultGroupByAccount:
            if res not in dataResult:
                dataResult[res] = { 'total': 0.0 }
            for line in resultGroupByAccount[res]:
                dataResult[res]['total'] += resultGroupByAccount[res][line]

        tag_16 = self.env.ref('l10n_mx.tag_diot_16')
        tag_non_cre = self.env.ref('l10n_mx.tag_diot_16_non_cre', raise_if_not_found=False) or self.env['account.account.tag']
        tag_8 = self.env.ref('l10n_mx.tag_diot_8', raise_if_not_found=False) or self.env['account.account.tag']
        tag_8_non_cre = self.env.ref('l10n_mx.tag_diot_8_non_cre', raise_if_not_found=False) or self.env['account.account.tag']
        tag_imp = self.env.ref('l10n_mx.tag_diot_16_imp')
        tag_0 = self.env.ref('l10n_mx.tag_diot_0')
        tag_ret = self.env.ref('l10n_mx.tag_diot_ret')
        tag_exe = self.env.ref('l10n_mx.tag_diot_exento')

        rep_line_obj =  self.env['account.tax.repartition.line'].with_context(active_test=False)
        purchase_tax_ids = self.env['account.tax'].with_context(active_test=False).search([('type_tax_use', '=', 'purchase')]).ids
        diot_common_domain = ['|', ('invoice_tax_id', 'in', purchase_tax_ids), ('refund_tax_id', 'in', purchase_tax_ids)]
        company = self.env.company.id

        # Line tax16
        account_tax16 = None
        tax16 = rep_line_obj.search([('tag_ids', 'in', tag_16.ids), ('company_id', '=', company)] + diot_common_domain).mapped('tax_id')
        for t16 in tax16.invoice_repartition_line_ids.mapped('account_id').filtered(lambda l: l != False):
            account_tax16 = t16

        # Line tax8
        account_tax8 = None
        tax8 = rep_line_obj.search([('tag_ids', 'in', tag_8.ids), ('company_id', '=', company)] + diot_common_domain).mapped('tax_id')
        for t8 in tax8.invoice_repartition_line_ids.mapped('account_id').filtered(lambda l: l != False):
            account_tax8 = t8

        account_tax8_noncre = None
        tax8_noncre = None
        if tag_8_non_cre:
            tax8_noncre = rep_line_obj.search([('tag_ids', 'in', tag_8_non_cre.ids), ('company_id', '=', company)] + diot_common_domain).mapped('tax_id')
            for t8No in tax8_noncre.invoice_repartition_line_ids.mapped('account_id').filtered(lambda l: l != False):
                account_tax8_noncre = t8No

        # Line tax8
        tax0 = rep_line_obj.search([('tag_ids', 'in', tag_0.ids), ('company_id', '=', company)] + diot_common_domain).mapped('tax_id')
        
        account_taxret = None
        tax_ret = rep_line_obj.search([('tag_ids', 'in', tag_ret.ids), ('company_id', '=', company)] + diot_common_domain).mapped('tax_id')
        for tret in tax_ret.invoice_repartition_line_ids.mapped('account_id').filtered(lambda l: l != False):
            account_taxret = tret

        line_partne_id = {}
        total_partner_id = {}
        total_moves_id = {}
        for line in lines:
            totalLineTax16 = 0

            # imprime Importe
            if line.get('id').startswith('partner_'):
                line_id = line["id"]
                partner_id = int( line_id.replace("partner_", "") )
                total_partner_id[ partner_id ] = {}
                if 'columns' in line:
                    name_tmp = {'name': '%s'%(self.format_value( dataResult[partner_id]['total'] )) }
                    line['columns'][4] = name_tmp

                    p_id = self.env['res.partner'].browse(partner_id)
                    moveLines = resultGroupByPartner.get( p_id ) and resultGroupByPartner[p_id].get('lines') or []
                    for move_line_id in moveLines:
                        total_moves_id[ move_line_id.id ] = {}

                        moveLineTax16, moveLineTax8, moveLineTax8No, moveLineTax0, moveLineTaxRet = 0.0, 0.0, 0.0, 0.0, 0.0
                        for imp in move_line_id.move_id.line_ids:

                            if imp.account_id == account_tax16 and imp.tax_line_id.id == tax16.id:
                                moveLineTax16 += imp.amount_currency
                                total_moves_id[ move_line_id.id ]['lineTax16'] = imp.amount_currency
                                total_moves_id[ move_line_id.id ]['partner_id'] = partner_id

                            if imp.account_id == account_tax8 and imp.tax_line_id.id == tax8.id:
                                moveLineTax8 += imp.amount_currency
                                total_moves_id[ move_line_id.id ]['lineTax8'] = imp.amount_currency
                                total_moves_id[ move_line_id.id ]['partner_id'] = partner_id

                            if imp.account_id == account_tax8_noncre and imp.tax_line_id.id == tax8_noncre.id:
                                moveLineTax8No += imp.amount_currency
                                total_moves_id[ move_line_id.id ]['lineTax8No'] = imp.amount_currency
                                total_moves_id[ move_line_id.id ]['partner_id'] = partner_id

                            if tax0.id in imp.tax_ids.ids and imp.tax_exigible == True:
                                moveLineTax0 += imp.amount_currency
                                total_moves_id[ move_line_id.id ]['lineTax0'] = imp.amount_currency
                                total_moves_id[ move_line_id.id ]['partner_id'] = partner_id

                            # print('---asdas ', imp.account_id, account_taxret, imp.tax_line_id.id, tax_ret.ids)
                            if imp.account_id in account_taxret and imp.tax_line_id.id in tax_ret.ids:
                                moveLineTaxRet += imp.amount_currency
                                total_moves_id[ move_line_id.id ]['lineTaxRet'] = imp.amount_currency
                                total_moves_id[ move_line_id.id ]['partner_id'] = partner_id

                        total_partner_id[ partner_id ]['totalLineTax16'] = moveLineTax16
                        total_partner_id[ partner_id ]['totalLineTax8'] = moveLineTax8
                        total_partner_id[ partner_id ]['totalLineTax8No'] = moveLineTax8No
                        total_partner_id[ partner_id ]['totalLineTax0'] = moveLineTax0
                        total_partner_id[ partner_id ]['totalLineTaxRet'] = moveLineTaxRet

            if line.get('caret_options'):
                move_line_id = self.env['account.move.line'].sudo().browse(int(line['id']))
                line['columns'][4] = {'name': '%s'%(self.format_value(move_line_id.amount_currency)) }

                move_tmp = total_moves_id.get( move_line_id.id )
                line['columns'][5] = {'name': '%s'%(self.format_value( move_tmp.get('lineTax16', 0.0) )) }
                line['columns'][7] = {'name': '%s'%(self.format_value( move_tmp.get('lineTax8', 0.0) )) } 
                line['columns'][8] = {'name': '%s'%(self.format_value( move_tmp.get('lineTax8No', 0.0) )) } 
                line['columns'][10] = {'name': '%s'%(self.format_value( move_tmp.get('lineTax0', 0.0) )) } 
                line['columns'][12] = {'name': '%s'%(self.format_value( move_tmp.get('lineTaxRet', 0.0) )) } 

            if line.get('id').startswith('total_'):
                partner_id = int( line["id"].replace("total_", "") )
                total_tmp = total_partner_id.get( partner_id )
                if 'columns' in line:
                    name_tmp = {'name': '%s'%(self.format_value( dataResult[partner_id]['total'] )) }
                    line['columns'][4] = name_tmp

                    total_16 = 0
                    for t16 in total_moves_id:
                        total_16 += total_moves_id[t16].get('lineTax16') or 0.0
                    name16_tmp = {'name': '%s'%(self.format_value( total_16 )) }
                    line['columns'][5] = name16_tmp

                    total_8 = 0
                    for t8 in total_moves_id:
                        total_8 += total_moves_id[t8].get('lineTax8') or 0.0
                    name8_tmp = {'name': '%s'%(self.format_value( total_8 )) }
                    line['columns'][7] = name8_tmp

                    total_8No = 0
                    for t8No in total_moves_id:
                        total_8No += total_moves_id[t8No].get('lineTax8No') or 0.0
                    name8No_tmp = {'name': '%s'%(self.format_value( total_8No )) }
                    line['columns'][8] = name8No_tmp

                    total_0 = 0
                    for t0 in total_moves_id:
                        total_0 += total_moves_id[t0].get('lineTax0') or 0.0
                    name0_tmp = {'name': '%s'%(self.format_value( total_0 )) }
                    line['columns'][10] = name0_tmp

                    total_ret = 0
                    for tret in total_moves_id:
                        total_ret += total_moves_id[tret].get('lineTaxRet') or 0.0
                    nameret_tmp = {'name': '%s'%(self.format_value( abs(total_ret) )) }
                    line['columns'][12] = nameret_tmp

            # imprime Importe
            if line.get('id').startswith('partner_'):
                partner_id = int( line["id"].replace("partner_", "") )
                if 'columns' in line:

                    total_16 = 0
                    for t16 in total_moves_id:
                        if total_moves_id[t16].get('partner_id') == partner_id: 
                            total_16 += total_moves_id[t16].get('lineTax16') or 0.0
                    name16_tmp = {'name': '%s'%(self.format_value( total_16 )) }
                    line['columns'][5] = name16_tmp

                    # TAX 8
                    total_8 = 0
                    for t8 in total_moves_id:
                        if total_moves_id[t8].get('partner_id') == partner_id: 
                            total_8 += total_moves_id[t8].get('lineTax8') or 0.0
                    name8_tmp = {'name': '%s'%(self.format_value( total_8 )) }
                    line['columns'][7] = name8_tmp

                    total_8No = 0
                    for t8No in total_moves_id:
                        if total_moves_id[t8No].get('partner_id') == partner_id: 
                            total_8No += total_moves_id[t8No].get('lineTax8No') or 0.0
                    name8No_tmp = {'name': '%s'%(self.format_value( total_8No )) }
                    line['columns'][8] = name8No_tmp

                    total_0 = 0
                    for t0 in total_moves_id:
                        if total_moves_id[t0].get('partner_id') == partner_id: 
                            total_0 += total_moves_id[t0].get('lineTax0') or 0.0
                    name0_tmp = {'name': '%s'%(self.format_value( total_0 )) }
                    line['columns'][10] = name0_tmp

                    total_ret = 0
                    for tret in total_moves_id:
                        if total_moves_id[tret].get('partner_id') == partner_id: 
                            total_ret += total_moves_id[tret].get('lineTaxRet') or 0.0
                    nameret_tmp = {'name': '%s'%(self.format_value( abs(total_ret) )) }
                    line['columns'][12] = nameret_tmp                    


        return lines


    @api.model
    def _get_report_name(self):
        return _('Reporte Impuestos DIO')

    def _get_reports_buttons(self):
        buttons = super(MxReportPartnerLedgerYeidala, self)._get_reports_buttons()
        # buttons += [{'name': _('Reporte Facturas - Impuestos'), 'sequence': 5, 'action': 'print_impuestos_txt', 'file_export_type': _('IMPUESTO')}]
        res = [i for i in buttons if not (i['action'] in ['print_dpiva_txt', 'print_txt'] )]
        return res

    def print_impuestos_txt(self, options):
        return {
            'type': 'ir_actions_account_report_download',
            'data': {
                'model': self.env.context.get('model'),
                'options': json.dumps(options),
                'output_format': 'txt',
                'financial_id': self.env.context.get('id'),
            }
        }

    def get_txt(self, options):
        ctx = self._set_context(options)
        return self.with_context(ctx)._l10n_mx_diot_print_impuestos_txt(options)


    def _l10n_mx_diot_print_impuestos_txt(self, options):
        tag_16 = self.env.ref('l10n_mx.tag_diot_16')
        rep_line_obj =  self.env['account.tax.repartition.line'].with_context(active_test=False)
        purchase_tax_ids = self.env['account.tax'].with_context(active_test=False).search([('type_tax_use', '=', 'purchase')]).ids
        diot_common_domain = ['|', ('invoice_tax_id', 'in', purchase_tax_ids), ('refund_tax_id', 'in', purchase_tax_ids)]
        company = self.env.company.id

        account_tax16 = None
        tax16 = rep_line_obj.search([('tag_ids', 'in', tag_16.ids), ('company_id', '=', company)] + diot_common_domain).mapped('tax_id')
        account_tax16 = tax16.cash_basis_transition_account_id

        lines = ''

        moveModel = self.env['account.move']
        move_ids = moveModel.search([('move_type', 'in', ['in_invoice', 'in_refund']), ('state', '=', 'posted')], order='invoice_date, partner_id')
        for move_id in move_ids:

            line_tax_ids = move_id.line_ids.mapped('tax_ids').filtered(lambda l:l.id == tax16.id)
            if not line_tax_ids:
                continue

            line_tax_ids = move_id.line_ids.filtered(lambda l: tax16.id == l.tax_line_id.id and l.account_id == account_tax16  )
            if not line_tax_ids:
                lines += '%s|%s|%s\n\r'%( move_id.partner_id.name,  move_id.name, move_id.invoice_date  )

        return lines