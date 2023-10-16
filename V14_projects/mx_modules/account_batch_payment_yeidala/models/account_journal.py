# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

import io
try:
    import xlwt
except ImportError:
    _logger.debug('Cannot `import xlwt`.')

class AccountJournal(models.Model):
    _inherit = "account.journal"

    file_generation_enabled = fields.Boolean(help="Whether or not this batch payment should display the 'Generate File' button instead of 'Print' in form view.")


class AccountMove(models.Model):
    _inherit = "account.move"

    def _compute_batch_bank_partner_id(self):
        if not self.partner_bank_id:
            bank_partner_id = self.partner_id.commercial_partner_id
            bank_ids = bank_partner_id.bank_ids.filtered(lambda bank: bank.company_id is False or bank.company_id == self.company_id)
            self.partner_bank_id = bank_ids and bank_ids[0]    

    def action_layout_payment_batch_banregio(self):
        datas = {}
        for rec in self.browse( self.env.context['active_ids'] ):
            if rec.partner_id.id not in datas:
                rec._compute_batch_bank_partner_id()
                cuenta = rec.partner_bank_id and rec.partner_bank_id.l10n_mx_edi_clabe or ''
                if rec.partner_bank_id and rec.partner_bank_id.bank_id.l10n_mx_edi_code == '058':
                    cuenta = rec.partner_bank_id and rec.partner_bank_id.acc_number or ''
                if not cuenta:
                    warning = 'El proveedor %s No tiene cuenta bancaria '%( rec.partner_id.name  )
                    raise UserError( warning )
                    break
        return {
            'type' : 'ir.actions.act_url',
            'url': '/web/report_layoutpaymentbatchbanregio?ids=%s'%( self.env.context['active_ids'] ),
            'target': 'self',
            'tag': 'reload',
        }

    def action_layout_payment_batch_banregio_datas(self):
        datas = {}
        indx = 1
        for rec in self:
            if rec.partner_id.id not in datas:
                tipo = 'S'
                cuenta = rec.partner_bank_id and rec.partner_bank_id.l10n_mx_edi_clabe or ''
                if rec.partner_bank_id and rec.partner_bank_id.bank_id.l10n_mx_edi_code == '058':
                    tipo = 'B'
                    cuenta = rec.partner_bank_id and rec.partner_bank_id.acc_number or ''
                datas[ rec.partner_id.id ] = {
                    'Secuencia': indx,
                    'Tipo': tipo,
                    'Cuenta_Destino': cuenta,
                    'Importe': 0,
                    'IVA': 0,
                    'Descripcion': 'Inv: ',
                    'Ref_Numerica': indx
                }
                indx += 1
            datas[ rec.partner_id.id ]['Importe'] += abs(rec.amount_residual_signed)
            datas[ rec.partner_id.id ]['Descripcion'] += ' %s'%(rec.ref or rec.invoice_origin or rec.name or '').replace('FACTU', '').replace('/', '')
        return self._generate_export_file(datas)

    def _generate_export_file(self, datas={}):
        workbook = xlwt.Workbook()
        stylePC = xlwt.XFStyle()
        alignment = xlwt.Alignment()
        alignment.horz = xlwt.Alignment.HORZ_CENTER
        fontP = xlwt.Font()
        fontP.bold = True
        fontP.height = 200
        stylePC.font = fontP
        stylePC.num_format_str = '@'
        stylePC.alignment = alignment
        style_title = xlwt.easyxf(
        "font:height 300; font: name Liberation Sans, bold on,color blue; align: horiz center")
        style_table_header = xlwt.easyxf("font:height 200; font: name Liberation Sans, bold on,color black; align: horiz center")
        style = xlwt.easyxf("font:height 200; font: name Liberation Sans,color black;")
        worksheet = workbook.add_sheet('Sheet 1')
        worksheet.write(0, 0, 'Secuencia', style_table_header)
        worksheet.write(0, 1, 'Tipo', style_table_header)
        worksheet.write(0, 2, 'Cuenta_Destino', style_table_header)
        worksheet.write(0, 3, 'Importe', style_table_header)
        worksheet.write(0, 4, 'IVA', style_table_header)
        worksheet.write(0, 5, 'Descripcion', style_table_header)
        worksheet.write(0, 6, 'Ref_Numerica', style_table_header)
        prod_row = 1
        prod_col = 0
        indx = 1        
        for line in datas:
            l = datas[line]
            indx = l['Secuencia']
            seq = '%s'%str(indx).zfill(5)
            worksheet.write(prod_row, prod_col, seq, style)
            worksheet.write(prod_row, prod_col+1, l['Tipo'], style)
            worksheet.write(prod_row, prod_col+2, '%s'%l['Cuenta_Destino'], style)
            worksheet.write(prod_row, prod_col+3, abs(l['Importe']), style)
            worksheet.write(prod_row, prod_col+4, 0.0, style)
            worksheet.write(prod_row, prod_col+5, '%s'%l['Descripcion'], style)
            worksheet.write(prod_row, prod_col+6, '%s'%( indx ), style)
            prod_row = prod_row + 1
            indx += 1
        filename = 'Transferencia_%s.xls'%(str(fields.Date.today()).replace('-','_'))
        fp = io.BytesIO()
        workbook.save(fp)
        return_datas = {
            'file': fp.getvalue(),
            'filename': filename,
        }
        return return_datas