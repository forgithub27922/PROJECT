# -*- coding: utf-8 -*-
import io
import os
import requests
import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)

class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.model_create_multi
    def create(self, vals_list):
        attachment_ids = super(IrAttachment, self).create(vals_list)
        for attachment_id in attachment_ids:
            if 'xml' in attachment_id.mimetype and attachment_id.res_model == 'account.move':
                inv = self.env[ attachment_id.res_model ].browse( attachment_id.res_id )
                inv.action_create_attachment_by_xml(attachment_id=attachment_id)
        return attachment_ids

class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_mx_edi_sat_emisor_rfc = fields.Char(string='Emisor RFC CFDI')
    l10n_mx_edi_sat_receptor_rfc = fields.Char(string='Receptor RFC CFDI')
    l10n_mx_edi_sat_foliofiscal = fields.Char(string='Folios Fiscal CFDI')
    l10n_mx_edi_sat_tipocomprobante = fields.Char(string='Tipo Compronte CFDI')
    l10n_mx_edi_sat_documento = fields.Char(string='Serie-Folio CFDI')
    l10n_mx_edi_sat_fecha = fields.Char(string='Fecha Pago CFDI')
    l10n_mx_edi_sat_monedap = fields.Char(string='Moneda Pago CFDI')
    l10n_mx_edi_sat_doctorel = fields.Char(string='Documento Relacionado CFDI')
    l10n_mx_edi_sat_montopago = fields.Float(string='Monto Pago CFDI')

    def action_create_attachment_by_xml(self, attachment_id=None):
        def get_node(cfdi_node, attribute, namespaces):
            if hasattr(cfdi_node, 'Complemento'):
                node = cfdi_node.Complemento.xpath(attribute, namespaces=namespaces)
                return node[0] if node else None
            else:
                return None

        if not attachment_id:
            attachment_id = self.l10n_mx_edi_retrieve_last_attachment_bfiskur()

        cfdi_edi_format = self.env.ref('l10n_mx_edi.edi_cfdi_3_3')
        cfdi_data = attachment_id._file_read(attachment_id.store_fname) if attachment_id else None
        xml_data = self._l10n_mx_edi_decode_cfdi(cfdi_data=cfdi_data)
        cfdi_node = xml_data.get('cfdi_node') or {}

        tipo_comprobante = cfdi_node.get('TipoDeComprobante')
        uuid = xml_data.get('uuid')
        if not uuid or tipo_comprobante != 'P':
            return {}

        ImpPagado = 0.0
        monedaP = 'MXN'
        fechaP = ''
        tfd_node = get_node(cfdi_node, 'tfd:TimbreFiscalDigital[1]', {'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'}, )
        pago10_node = get_node(cfdi_node, 'pago10:Pagos[1]', {'pago10': 'http://www.sat.gob.mx/Pagos'}, )
        for pago10 in pago10_node.iterchildren():
            fechaP = pago10.get('FechaPago')
            monedaP = pago10.get('MonedaP')
            for pagosDocto in pago10.iterchildren():
                ImpPagado = float(pagosDocto.get('ImpPagado', '0.0'))
                IdDocumento = pagosDocto.get('IdDocumento')
                doctorel_id = self.search([
                    ('l10n_mx_edi_sat_uuid', '=', IdDocumento),
                    ('company_id', '=', self.env.user.company_id.id),
                    ('move_type', 'in', ['in_invoice', 'in_refund']), 
                    ('state', 'in', ['cancel', 'posted']), 
                ])
                status = ''
                try:
                    statussat = self.env['account.edi.format']._l10n_mx_edi_get_sat_status(xml_data.get('supplier_rfc'), xml_data.get('customer_rfc'), '0.0', uuid)
                    if statussat == 'Vigente':
                        status = 'valid'
                    elif statussat == 'Cancelado':
                        status = 'cancelled'
                    elif statussat == 'No Encontrado':
                        status = 'not_found'
                    else:
                        status = 'none'
                except Exception as e:
                    status = ''
                    pass
                self.update({
                    'l10n_mx_edi_sat_emisor_rfc': xml_data.get('supplier_rfc'),
                    'l10n_mx_edi_sat_receptor_rfc': xml_data.get('customer_rfc'),
                    'l10n_mx_edi_sat_foliofiscal': uuid,
                    'l10n_mx_edi_sat_uuid': uuid,
                    'l10n_mx_edi_sat_tipocomprobante': tipo_comprobante,
                    'l10n_mx_edi_sat_documento': '%s%s'%( cfdi_node.get('Serie', ''), cfdi_node.get('Folio', '') ),
                    'l10n_mx_edi_sat_fecha': fechaP,
                    'l10n_mx_edi_sat_monedap': monedaP,
                    'l10n_mx_edi_sat_doctorel': IdDocumento,
                    'l10n_mx_edi_sat_montopago': ImpPagado,
                    'l10n_mx_edi_sat_status': status
                })
        return {}


    """
    l10n_mx_edi_sat_total = fields.Float(string='Total Inv', help='subtotal.')
    l10n_mx_edi_sat_subtotal = fields.Float(string='Subtotal Inv', help='subtotal.')
    l10n_mx_edi_sat_descuento = fields.Float(string='Descuento Inv', help='descuento.')
    l10n_mx_edi_sat_serie = fields.Char(string='Serie Inv', help='Serie.')
    l10n_mx_edi_sat_folio = fields.Char(string='Folio Inv', help='Folio.')
    l10n_mx_edi_sat_tipocambio = fields.Float(string='Tipo Cambio Inv', help='Tipo Cambio.')
    def l10n_mx_edi_decode_cfdi(self, cfdi_data=None):
        data = self._l10n_mx_edi_decode_cfdi(cfdi_data=cfdi_data)
        cfdi_node = data.get('cfdi_node') or {}
        for move in self:
            self.update({
                'l10n_mx_edi_sat_total': float( cfdi_node.get('Total', '0.0') ),
                'l10n_mx_edi_sat_subtotal': float( cfdi_node.get('SubTotal', '0.0') ),
                'l10n_mx_edi_sat_descuento': float( cfdi_node.get('Descuento', '0.0') ),
                'l10n_mx_edi_sat_tipocambio': float( cfdi_node.get('TipoCambio', '1') ),
                'l10n_mx_edi_sat_serie': cfdi_node.get('Serie', ''),
                'l10n_mx_edi_sat_folio': cfdi_node.get('Folio', ''),
            })
        return data
    http://marthapc:8099/web?debug=1#id=208358&model=account.move&view_type=form&cids=12&menu_id=164

    """

    @api.model
    def l10n_mx_edi_retrieve_attachments_bfiskur(self):
        self.ensure_one()
        domain = [
            ('res_id', '=', self.id),
            ('res_model', '=', self._name),
            ('name', 'ilike', '.xml')]
        return self.env['ir.attachment'].search(domain)

    @api.model
    def l10n_mx_edi_retrieve_last_attachment_bfiskur(self):
        attachment_ids = self.l10n_mx_edi_retrieve_attachments_bfiskur()
        return attachment_ids and attachment_ids[0] or None



    def get_txt(self, options):
        body = options.get("datas", "")
        encoding = options.get("encoding", "utf-8")
        output = io.BytesIO()
        output.write(b'%s'%body.encode(encoding))
        output.seek(0)
        generated_file = output.read()
        output.close()
        return generated_file

    def action_bfiskur_texto(self, datas_out=[]):
        lines_count = len(datas_out)
        lines = ''
        for indx, data in enumerate(datas_out):
            break_line = ''
            if (indx+1) != lines_count:
                break_line = '\n'
            lines += '|'.join(str(d) for d in data) + break_line
        return lines

    def action_bfiskur_api(self, cid, filename, datas_out=[]):
        cia_id = self.env['res.company'].browse(cid)
        headers = {
            "Accept": "*/*", 
            "Accept-Encoding": "gzip, deflate", 
            "Content-Length": "189", 
            "Content-Type": "multipart/form-data; boundary=53bb41eb09d784cedc62d521121269f8", 
            "Host": "httpbin.org", 
            "User-Agent": "python-requests/2.25.0", 
            "X-Amzn-Trace-Id": "Root=1-5fc3c190-5dea2c7633a02bcf5e654c2b"
        }
        values={
            'userEmail' : cia_id.bfiskur_username, 
            'userPassword': cia_id.bfiskur_password, 
            "FieldDelimiter": "|", 
            "asTxtFile": 1, 
            "isUTF8": 1
        }
        filetxt = self.get_txt({
            'datas': self.action_bfiskur_texto(datas_out),
            'encoding': 'utf-8'
        })
        # text_file = open("/tmp/enviados.csv", "w")
        # text_file.write(filetxt.decode('utf-8'))
        # text_file.close()

        files= {'file': ("%s.csv"%filename, filetxt, 'multipart/form-data', {'Expires': '0'}) }
        with requests.Session() as s:
            r = s.post(cia_id.bfiskur_url, files=files, params=values)
            _logger.info('---- Bfiskur status_code %s - %s '%( r.status_code, r.text ) )
        return True


    def action_bfiskur_setdata(self, cia_id=None, data_type="", date_start=None, date_end=None):
        datas = getattr(self, 'action_bfiskur_setdata_%s'%(data_type) )(cia_id, date_start, date_end)
        return datas



    def action_bfiskur_setdata_pagosrecibidos(self, cia_id, date_start, date_end):
        cfdi_edi_format = self.env.ref('l10n_mx_edi.edi_cfdi_3_3')
        header_out = [
            'RFC Compañia',
            'Proveedor Key',
            'Proveedor',
            'Documento pago Key',
            'Documento pago',
            'Estatus Key',
            'Fecha cancelación',
            'Moneda Key',
            'Documento relacionado Key',
            'DateID',
            'Monto pago',
            'Tipo de cambio pago'
        ]
        where = [
            ('company_id', '=', cia_id),
            ('state', 'in', ['cancel', 'posted']), 
            ('l10n_mx_edi_sat_tipocomprobante', '=', 'P'), 
            ('l10n_mx_edi_sat_foliofiscal', '!=', False), 
            ('date', '>=', date_start), 
            ('date', '<=', date_end)
        ]
        move_ids = self.search(where)
        datas_out = []
        datas_out.append(header_out)
        file_name = ""
        for move in move_ids:
            file_name = "%s_pagos_recibidos"%(move.company_id.vat)
            fechaP = move.l10n_mx_edi_sat_fecha.split('T')
            datas_tmp = [
                "%s"%( move.company_id.vat ),                                       # 1
                "%s"%( move.partner_id.vat ),                                       # 2
                "%s"%( move.partner_id.name ),                                      # 3
                "%s"%( move.l10n_mx_edi_sat_foliofiscal ),                          # 4
                "%s"%( move.l10n_mx_edi_sat_documento ),                            # 5
                "%s"%( 1 if move.l10n_mx_edi_sat_status != 'cancelled' else 0 ),    # 6
                '',                                                                 # 7
                "%s"%( move.currency_id.name ),                                     # 8
                "%s"%( move.l10n_mx_edi_sat_doctorel ),                             # 9
                "%s"%( fechaP[0] if len(fechaP) > 1 else ''),                       # 10
                "%s"%( move.amount_total ),                                         # 11
                "%s"%( 1 ),                                                         # 12
            ]
            datas_out.append(datas_tmp)
        return self.action_bfiskur_api(cia_id, file_name, datas_out)

    def action_bfiskur_setdata_cfdirecibidos(self, cia_id, date_start, date_end):
        cfdi_edi_format = self.env.ref('l10n_mx_edi.edi_cfdi_3_3')
        header_out = [
            u"RFC Compañia",                # 01
            "Tipo Proveedor",               # 02
            "Proveedor Key",                # 03
            "Proveedor",                    # 04
            "Tipo de Documento Key",        # 05
            "Documento Key",                # 06
            "Documento",                    # 07
            "Moneda Key",                   # 08
            "Documento Relacionado Key",    # 09
            "Metodo pago Key",              # 10
            "Estatus Key",                  # 11
            u"Fecha cancelación",           # 12
            "DateID",                       # 13
            "Subtotal",                     # 14
            "Descuentos",                   # 15
            "Tipo de cambio",               # 16
            "IEPS retenido",                # 17
            "IEPS acreditable",             # 18
            "ISR retenido",                 # 19
            "IVA retenido",                 # 20
            "IVA acreditable",              # 21
            "Impuesto local retenido",      # 22
            "Impuesto local acreditable"    # 23
        ]
        where = [
            ('company_id', '=', cia_id),
            ('move_type', 'in', ['in_invoice', 'in_refund']), 
            ('state', 'in', ['cancel', 'posted']), 
            ('l10n_mx_edi_sat_uuid', '!=', False), 
            ('invoice_date', '>=', date_start), 
            ('invoice_date', '<=', date_end)
        ]
        move_ids = self.search(where)
        datas_out = []
        datas_out.append(header_out)
        file_name = ""
        for move in move_ids:
            file_name = "%s_docs_recibidos"%(move.company_id.vat)
            if move.name == '/':
                continue
            datasFormat = cfdi_edi_format._l10n_mx_edi_get_invoice_cfdi_values(move)
            if not datasFormat:
                continue
            taxes = {
                'ISR': 0.0,
                'ISR_RET': 0.0,
                'IVA': 0.0,
                'IVA_RET': 0.0,
                'IEPS': 0.0,
                'IEPS_RET': 0.0
            }
            for transferred in datasFormat.get('tax_details_transferred', []):
                tax = transferred.get('tax')
                if tax.tax_group_id.name.find('IVA') >= 0:
                    taxes['IVA'] += transferred.get('total')
                if tax.tax_group_id.name.find('ISR') >= 0:
                    taxes['ISR'] += transferred.get('total')
                if tax.tax_group_id.name.find('IEPS') >= 0:
                    taxes['IEPS'] += transferred.get('total')
            for withholding in datasFormat.get('tax_details_withholding', []):
                tax = withholding.get('tax')
                if tax.tax_group_id.name.find('IVA') >= 0:
                    taxes['IVA_RET'] += withholding.get('total')
                if tax.tax_group_id.name.find('ISR') >= 0:
                    taxes['ISR_RET'] += withholding.get('total')
                if tax.tax_group_id.name.find('IEPS') >= 0:
                    taxes['IEPS_RET'] += withholding.get('total')
            origin_uuid = ''
            if move.l10n_mx_edi_origin:
                origin_type, origin_uuids = move._l10n_mx_edi_read_cfdi_origin(move.l10n_mx_edi_origin)
                for origin in origin_uuids:
                    origin_uuid = origin
            partner_type = 'Nacional' if move.partner_id.country_id.code == 'MX' else 'Extranjero'
            documento = '%s%s'%( datasFormat.get('serie_number'), datasFormat.get('folio_number') )
            estatus_key = 0 if move.l10n_mx_edi_sat_status == 'cancelled' else 1
            subtotal = datasFormat.get('total_amount_untaxed_wo_discount', 0)
            descuento = datasFormat.get('total_amount_untaxed_discount', 0)
            tipocambio = 1 if datasFormat.get('currency_conversion_rate') in ["", False, None] else datasFormat.get('currency_conversion_rate')
            iva_ret = datasFormat.get('total_tax_details_withholding', 0)
            iva_tras = datasFormat.get('total_tax_details_transferred', 0)
            datas_tmp = [
                "%s"%( move.company_id.vat ),                       # 1
                "%s"%(partner_type),                                # 2
                "%s"%( move.partner_id.vat ),                       # 3
                "%s"%( move.partner_id.name ),                      # 4
                "%s"%( datasFormat.get('document_type', 'I') ),     # 5
                "%s"%( move.l10n_mx_edi_sat_uuid ),                 # 6
                "%s"%( documento ),                                 # 7
                "%s"%( datasFormat.get('currency_name') ),          # 8
                "%s"%( origin_uuid ),                               # 9
                "%s"%( datasFormat.get('payment_policy', 'PPD') ),  # 10
                "%s"%( estatus_key ),                               # 11
                "%s"%( "" ),                                        # 12
                "%s"%( move.invoice_date ),                         # 13
                "%s"%( subtotal ),                                  # 14
                "%s"%( descuento ),                                 # 15
                "%s"%( tipocambio ),                                # 16
                "%s"%( abs(taxes.get('IEPS_RET') )),                # 17
                "%s"%( taxes.get('IEPS') ),                         # 18
                "%s"%( abs(taxes.get('ISR_RET') )),                 # 19
                "%s"%( abs(taxes.get('IVA_RET') )),                 # 20
                "%s"%( taxes.get('IVA') ),                          # 21
                "%s"%( 0 ),                                         # 22
                "%s"%( 0 ),                                         # 23
            ]
            datas_out.append(datas_tmp)
        return self.action_bfiskur_api(cia_id, file_name, datas_out)


    def action_bfiskur_setdata_cfdiemitidos(self, cia_id, date_start, date_end):
        cfdi_edi_format = self.env.ref('l10n_mx_edi.edi_cfdi_3_3')
        header_out = [u"RFC Compañia", u"Cliente Key", u"Cliente", u"Tipo de Documento Key", u"Documento Key", "Documento", "Documento relacionado Key", "Moneda Key", "Metodo pago Key", "Estatus Key", u"Fecha cancelación", "DateID", "Subtotal", "Descuentos", "Tipo de cambio", "IEPS retenido", "IEPS trasladado", "ISR retenido", "IVA retenido", "IVA trasladado", "Impuesto local retenido", "Impuesto local trasladado"]
        where = [
            ('company_id', '=', cia_id),
            ('move_type', 'in', ['out_invoice', 'out_refund']), 
            ('state', 'in', ['cancel', 'posted']), 
            ('l10n_mx_edi_sat_uuid', '!=', False), 
            ('invoice_date', '>=', date_start), 
            ('invoice_date', '<=', date_end),
        ]
        move_ids = self.search(where)
        datas_out = []
        datas_out.append(header_out)
        file_name = ""
        for move in move_ids:
            file_name = "%s_docs_emitidos"%(move.company_id.vat)
            datasFormat = cfdi_edi_format._l10n_mx_edi_get_invoice_cfdi_values(move)
            origin_uuid = ''
            if move.l10n_mx_edi_origin:
                origin_type, origin_uuids = move._l10n_mx_edi_read_cfdi_origin(move.l10n_mx_edi_origin)
                for origin in origin_uuids:
                    origin_uuid = origin
            taxes = {
                'ISR': 0.0,
                'ISR_RET': 0.0,
                'IVA': 0.0,
                'IVA_RET': 0.0,
                'IEPS': 0.0,
                'IEPS_RET': 0.0
            }
            for transferred in datasFormat.get('tax_details_transferred', []):
                if transferred.get('tax_name') == '001':
                    taxes['ISR'] += transferred.get('total')
                if transferred.get('tax_name') == '002':
                    taxes['IVA'] += transferred.get('total')
                if transferred.get('tax_name') == '003':
                    taxes['IEPS'] += transferred.get('total')
            for withholding in datasFormat.get('tax_details_withholding', []):
                if withholding.get('tax_name') == '001':
                    taxes['ISR_RET'] += withholding.get('total')
                if withholding.get('tax_name') == '002':
                    taxes['IVA_RET'] += withholding.get('total')
                if withholding.get('tax_name') == '003':
                    taxes['IEPS_RET'] += withholding.get('total')
            documento = '%s%s'%( datasFormat.get('serie_number'), datasFormat.get('folio_number') )
            estatus_key = 0 if move.l10n_mx_edi_sat_status == 'cancelled' else 1
            subtotal = datasFormat.get('total_amount_untaxed_wo_discount', 0)
            descuento = datasFormat.get('total_amount_untaxed_discount', 0)
            tipocambio = 1 if datasFormat.get('currency_conversion_rate') in ["", False, None] else datasFormat.get('currency_conversion_rate')
            iva_ret = datasFormat.get('total_tax_details_withholding', 0)
            iva_tras = datasFormat.get('total_tax_details_transferred', 0)
            datas_tmp = [
                "%s"%( move.company_id.vat ),                       # 1
                "%s"%( move.partner_id.vat ),                       # 2
                "%s"%( move.partner_id.name ),                      # 3
                "%s"%( datasFormat.get('document_type', 'I') ),     # 4
                "%s"%( move.l10n_mx_edi_sat_uuid ),                 # 5
                "%s"%( documento ),                                 # 6
                "%s"%( origin_uuid ),                               # 7
                "%s"%( datasFormat.get('currency_name') ),          # 8
                "%s"%( datasFormat.get('payment_policy', 'PPD') ),  # 9,
                "%s"%( estatus_key ),                               # 10
                "%s"%( "" ),                                        # 11
                "%s"%( move.invoice_date ),                         # 12
                "%s"%( subtotal ),                                  # 13
                "%s"%( descuento ),                                 # 14
                "%s"%( tipocambio ),                                # 15
                "%s"%( taxes.get('IEPS_RET') ),                     # 16
                "%s"%( taxes.get('IEPS') ),                         # 17
                "%s"%( taxes.get('ISR_RET') ),                      # 18
                "%s"%( taxes.get('IVA_RET') ),                      # 19
                "%s"%( taxes.get('IVA') ),                          # 20
                "%s"%( 0 ),                                         # 21
                "%s"%( 0 ),                                         # 22
            ]
            datas_out.append(datas_tmp)
        return self.action_bfiskur_api(cia_id, file_name, datas_out)



    def action_bfiskur_setdata_pagosemitidos(self, cia_id, date_start, date_end):
        where = [
            ('company_id', '=', cia_id),
            ('state', 'in', ['cancel', 'posted']), 
            ('l10n_mx_edi_post_time', '>=', '%s 00:00:00'%date_start), 
            ('l10n_mx_edi_post_time', '<=', '%s 23:59:59'%date_end),
            ('payment_id', '!=', False),
            ('payment_id.payment_type', '=', 'inbound'),
            ('payment_id.partner_type', '=', 'customer'),
            ('l10n_mx_edi_sat_uuid', '!=', False)
        ]
        move_ids = self.search(where)
        header_out = [u"RFC Compañia",u"Cliente Key", u"Cliente", u"Documento pago Key", u"Documento pago", u"Estatus Key", u"Fecha cancelación", u"Moneda Key", u"Documento relacionado Key", u"DateID", u"Monto pago", u"Tipo de cambio pago"]
        datas_out = []
        datas_out.append(header_out)
        cfdi_edi_format = self.env.ref('l10n_mx_edi.edi_cfdi_3_3')
        file_name=""
        for move in move_ids:
            file_name = "%s_pagos_emitidos"%(move.company_id.vat)
            datasFormat = cfdi_edi_format._l10n_mx_edi_export_payment_cfdi_datas(move)
            
            origin_uuid, moneda = "", ""
            monto_pago = 0.0
            tipocambio = 1
            for invoice_vals in datasFormat.get('invoice_vals_list', []):
                monto_pago = invoice_vals['amount_paid']
                tipocambio = 1 if invoice_vals['exchange_rate'] == None else invoice_vals['exchange_rate']
                for invoice in invoice_vals.get("invoice"):
                    origin_uuid = invoice.l10n_mx_edi_cfdi_uuid or ''
                    moneda = invoice.currency_id.name
            documento = '%s%s'%( datasFormat.get('serie_number'), datasFormat.get('folio_number') )
            estatus_key = 0 if move.l10n_mx_edi_sat_status == 'cancelled' else 1
            cfdi_payment_date = ("%s"%datasFormat.get('cfdi_payment_date')).split("T")
            currency = datasFormat.get('currency')
            datas_tmp = [
                "%s"%( move.company_id.vat ),                       # 1
                "%s"%( move.partner_id.vat ),                       # 2
                "%s"%( move.partner_id.name ),                      # 3
                "%s"%( move.l10n_mx_edi_sat_uuid ),                 # 4
                "%s"%( documento ),                                 # 5
                "%s"%( estatus_key ),                               # 6
                "%s"%( "" ),                                        # 7
                "%s"%( moneda ),                                    # 8
                "%s"%( origin_uuid ),                               # 9
                "%s"%( cfdi_payment_date[0] ),                      # 10
                "%s"%( monto_pago ),                                # 11
                "%s"%( tipocambio ),                                # 12
            ]
            datas_out.append(datas_tmp)
        return self.action_bfiskur_api(cia_id, file_name, datas_out)



# curl --insecure -o "response.html" -F xmlDocs=@BME000904N18_Emitidos.zip -F TipoXML=Emitidos -F usuario=sistemas@ejemplo.com.mx -F password=abcde https://kpionline5.bitam.com/fbm/bfiskurERPCarga/service.php
"""
# -*- coding: utf-8 -*-

import odoorpc
odoo = odoorpc.ODOO('localhost', port=8099)
odoo.login('odoo14_pplog', 'yeidala@plog.com.mx', 'g6SW29KelCch')
MoveModel = odoo.env['account.move']
move_id = MoveModel.browse(116307)
move_id.l10n_mx_edi_decode_cfdi()
move_id.getDatasBFiskur()
"""