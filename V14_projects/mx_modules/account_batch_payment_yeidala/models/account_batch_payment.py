# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import re
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

import io
try:
    import xlwt
except ImportError:
    _logger.debug('Cannot `import xlwt`.')

import logging
_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.model
    def _get_method_codes_using_bank_account(self):
        result = super(AccountPayment, self)._get_method_codes_using_bank_account()
        result.extend(['batch_payment', 'layout_payment'])
        return result

    @api.model
    def _get_method_codes_needing_bank_account(self):
        result = super(AccountPayment, self)._get_method_codes_needing_bank_account()
        result.extend(['batch_payment', 'layout_payment'])
        return result  

    def _compute_batch_bank_partner_id(self):
        if not self.partner_bank_id:
            bank_partner_id = self.partner_id.commercial_partner_id
            bank_ids = bank_partner_id.bank_ids.filtered(lambda bank: bank.company_id is False or bank.company_id == self.company_id)
            self.partner_bank_id = bank_ids and bank_ids[0]


class AccountBatchPayment(models.Model):
    _inherit = "account.batch.payment"
    _description = "Batch Payment"

    def _get_methods_generating_files(self):
        rec = super(AccountBatchPayment, self)._get_methods_generating_files()
        rec.append('layout_payment')
        return rec

    def _generate_export_file(self):
        datas = '01|02|03|04\n\r01|02|03|04'
        for record in self:
            if record.payment_method_id.code == 'layout_payment':
                warning = ''
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
                for line in record.payment_ids:
                    line._compute_batch_bank_partner_id()
                    tipo = 'S'
                    cuenta = line.partner_bank_id and line.partner_bank_id.l10n_mx_edi_clabe or ''
                    if line.partner_bank_id and line.partner_bank_id.bank_id.l10n_mx_edi_code == '058':
                        tipo = 'B'
                        cuenta = line.partner_bank_id and line.partner_bank_id.acc_number or ''
                    if not cuenta:
                        warning = 'El proveedor %s No tiene cuenta bancaria '%( line.partner_id.name  )
                        break
                    seq = '%s'%str(indx).zfill(5)
                    refs = [int(s) for s in re.findall(r'-?\d+\.?\d*', line.name.replace('/', ' '))]
                    ref = ''.join(map(str, refs))
                    worksheet.write(prod_row, prod_col, seq, style)
                    worksheet.write(prod_row, prod_col+1, tipo, style)
                    worksheet.write(prod_row, prod_col+2, '%s'%cuenta, style)
                    worksheet.write(prod_row, prod_col+3, abs(line.amount), style)
                    worksheet.write(prod_row, prod_col+4, 0.0, style)
                    worksheet.write(prod_row, prod_col+5, '%s'%line.ref, style)
                    worksheet.write(prod_row, prod_col+6, '%s'%( ref ), style)
                    prod_row = prod_row + 1
                    indx += 1

                filename = 'Transferencia_%s.xls'%(str(record.date).replace('-','_'))
                fp = io.BytesIO()
                workbook.save(fp)
                return_datas = {
                    'file': base64.encodestring(fp.getvalue()),
                    'filename': filename,
                }
                if warning:
                    raise UserError( warning )
                return return_datas
        return False
