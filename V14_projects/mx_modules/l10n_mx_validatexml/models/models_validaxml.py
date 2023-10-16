# -*- coding: utf-8 -*-

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

class MyLoggingPlugin(Plugin):
    def ingress(self, envelope, http_headers, operation):
        logging.info( etree.tostring(envelope, pretty_print=True) )
        return envelope, http_headers

    def egress(self, envelope, http_headers, operation, binding_options):
        logging.info( etree.tostring(envelope, pretty_print=True) )
        return envelope, http_headers

def get_attachment_content(attachment):
    cfdi = base64.b64decode(attachment).decode()
    cfdi = cfdi.replace('xmlns:schemaLocation', 'xsi:schemaLocation')
    indx = cfdi.find('</cfdi:Comprobante>')
    cfdi = cfdi[0:indx+19]
    xml_signed = base64.b64encode(cfdi.encode('utf-8'))
    return xml_signed

class AccountEdiFormat(models.Model):
    _inherit = 'account.edi.format'

    def _create_cfdi_attachment(self, cfdi_filename, description, move, data):
        IrAttachment = self.env['ir.attachment']
        values = {
            'name': cfdi_filename,
            'res_id': move.id,
            'res_model': move._name,
            'type': 'binary',
            'datas': data,
            'mimetype': 'application/xml',
            'description': description,
        }
        attachment = IrAttachment.search([('name', '=', cfdi_filename), ('res_model', '=', move._name), ('res_id', '=', move.id), ('type', '=', 'binary')])
        if attachment:
            attachment.write(values)
            return attachment[0]
        else:
            return IrAttachment.create(values)

class AccountTaxGroup(models.Model):
    _inherit = 'account.tax.group'

    l10n_mx_edi_imploc = fields.Boolean(string='Es Impuesto Local?', help='Impuesto Local.')

class AccountMove(models.Model):
    _inherit = 'account.move'

    def _compute_l10n_mx_edi_amount_untaxed_wo_discount(self):
        invoice_lines = self.invoice_line_ids.filtered(lambda inv: not inv.display_type)
        invoice_line_values = []
        for line in invoice_lines:
            invoice_line_values.append(self._l10n_mx_edi_get_invoice_line_cfdi_values_xml(line))
        total_amount_untaxed_wo_discount = sum(vals['total_wo_discount'] for vals in invoice_line_values)
        self.l10n_mx_edi_amount_untaxed_wo_discount = total_amount_untaxed_wo_discount

    l10n_mx_edi_amount_untaxed_wo_discount = fields.Monetary(string='Amount Untaxed Without Discount', copy=False, readonly=True,
        help='The total amount reported on the cfdi.',
        compute='_compute_l10n_mx_edi_amount_untaxed_wo_discount')

    l10n_mx_edi_sat_uuid = fields.Char(string='UUID Inv', help='Folio in electronic invoice, is returned by SAT when send to stamp.')
    ocultar_validaxml = fields.Boolean(default=False, copy=False, compute='_compute_ocultar_validaxml')
    creada_de_xml = fields.Boolean(string="Creada a partir de CFDI", default=False, copy=False)

    def action_validar_xml(self):
        context = dict(self.env.context or {})
        context['active_ids'] = [self.id]
        context['active_id'] = self.id
        context["active_model"] = "account.move"
        data_obj = self.env['ir.model.data']
        view = data_obj.xmlid_to_res_id('l10n_mx_validatexml.account_invoice_cfdiupload_form_view')
        wiz_id = self.env['account.invoice.cfdiupload'].create({})
        return {
             'name': _('Subir XML y PDF'),
             'type': 'ir.actions.act_window',
             'view_type': 'form',
             'view_mode': 'form',
             'res_model': 'account.invoice.cfdiupload',
             'views': [(view, 'form')],
             'view_id': view,
             'target': 'new',
             'res_id': wiz_id.id,
             'context': context,
         }

    def _compute_ocultar_validaxml(self):
        for move in self:
            if move.is_purchase_document(include_receipts=True):
                move.ocultar_validaxml = False
                continue
            move.ocultar_validaxml = True

    @api.depends('edi_document_ids')
    def _compute_cfdi_values(self):
        res = super()._compute_cfdi_values()
        for move in self:
            move.l10n_mx_edi_sat_uuid = move.l10n_mx_edi_cfdi_uuid
        return res

    def _l10n_mx_edi_get_invoice_line_cfdi_values_xml(self, line):
        cfdi_values = {'line': line}
        cfdi_values['price_unit_wo_discount'] = line.price_unit * (1 - (line.discount / 100.0))
        if line.discount != 100.0:
            gross_price_subtotal = self.currency_id.round(line.price_subtotal / (1 - line.discount / 100.0))
        else:
            gross_price_subtotal = self.currency_id.round(line.price_unit * line.quantity)
        cfdi_values['discount_amount'] = gross_price_subtotal - line.price_subtotal
        cfdi_values['total_wo_discount'] = gross_price_subtotal
        cfdi_values['price_subtotal_unit'] = self.currency_id.round(
            cfdi_values['total_wo_discount'] / line.quantity) if line.quantity else 0
        # ==== Taxes ====
        tax_details = line.tax_ids.compute_all(
            cfdi_values['price_unit_wo_discount'],
            currency=line.currency_id,
            quantity=line.quantity,
            product=line.product_id,
            partner=line.partner_id,
            is_refund=self.move_type in ('out_refund', 'in_refund'),
        )
        cfdi_values['tax_details'] = {}
        for tax_res in tax_details['taxes']:
            if tax_res['base'] == 0:
                continue
            tax = self.env['account.tax'].browse(tax_res['id'])
            tax_rep_field = 'invoice_repartition_line_ids' if self.move_type == 'out_invoice' else 'refund_repartition_line_ids'
            tags = tax[tax_rep_field].tag_ids
            tax_name = {'ISR': '001', 'IVA': '002', 'IEPS': '003'}.get(tags.name) if len(tags) == 1 else None
            cfdi_values['tax_details'].setdefault(tax, {
                'tax': tax,
                'base': tax_res['base'],
                'tax_type': tax.l10n_mx_tax_type,
                'tax_amount': tax.amount / 100.0 if tax.amount_type != 'fixed' else tax.amount / tax_res['base'],
                'tax_name': tax_name,
                'total': 0.0,
            })
            cfdi_values['tax_details'][tax]['total'] += tax_res['amount']
        cfdi_values['tax_details'] = list(cfdi_values['tax_details'].values())
        cfdi_values['tax_details_transferred'] = [tax_res for tax_res in cfdi_values['tax_details'] if tax_res['tax_amount'] >= 0.0]
        cfdi_values['tax_details_withholding'] = [tax_res for tax_res in cfdi_values['tax_details'] if tax_res['tax_amount'] < 0.0]
        return cfdi_values

class AccountInvoiceCfdiUpload(models.TransientModel):
    _name = 'account.invoice.cfdiupload'
    _description = "Account Invoice XML Upload"

    attachment_ids = fields.Many2many('ir.attachment', string='Files')
    move_id = fields.Many2one(string="Facturas", comodel_name="account.move")
    reporte_validation_xml = fields.Html("Reporte Validar XML")
    message_validation_xml = fields.Html("Mensaje Validar XML")
    codigo = fields.Char(string="Codigo Estatus")
    estado = fields.Char(string="Estado")
    uuid = fields.Char(string="UUID")
    invoice_date = fields.Date(string='Fecha')
    serie = fields.Char(string="Serie")
    folio = fields.Char(string="folio")
    errorvalidacion = fields.Boolean(string='Error en Validacion')
    uui_duplicado = fields.Boolean(string="UUID Duplicado", default=False)
    act_next = fields.Boolean(string="Continuar", default=False)
    company_id = fields.Many2one('res.company', string='Company', 
        required=True, readonly=True, copy=False, 
        default=lambda self: self.env['res.company']._company_default_get())

    @api.model
    def l10n_mx_edi_get_tfd_etree(self, cfdi):
        if not hasattr(cfdi, 'Complemento'):
            return None
        attribute = 'tfd:TimbreFiscalDigital[1]'
        namespace = {'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'}
        node = cfdi.Complemento.xpath(attribute, namespaces=namespace)
        return node[0] if node else None

    @api.model
    def get_xml_datas(self, cfdi):
        Emisor = cfdi.Emisor
        Receptor = cfdi.Receptor
        tfd = self.l10n_mx_edi_get_tfd_etree(cfdi)
        res = {
            'serie': cfdi.get('Serie'), 
            'folio': cfdi.get('Serie'), 
            'importe_total': cfdi.get('Total'),
            'importe_subtotal': cfdi.get('SubTotal'),
            'version': cfdi.get('Version'),
            'tipo_comprobante': cfdi.get('TipoDeComprobante'),
            'certificado_emisor': cfdi.get('NoCertificado'),
            'fecha_emision': cfdi.get('Fecha'),
            'nombre_emisor': Emisor.get('Nombre'),
            'rfc_emisor': Emisor.get('Rfc'),
            'nombre_receptor': Receptor.get('Nombre'),
            'rfc_receptor': Receptor.get('Rfc'),
            'certificado_sat': tfd.get("noCertificadoSAT") or "",
            'fecha_certificacion': tfd.get("FechaTimbrado") or "",
            'uuid': tfd.get('UUID'),
        }
        return res

    @api.model
    def _reporte_validacion_xml(self, xml_datas):
        validar_xml = u"""
        <div class="card">
            <div class="card-body">
                <div class="container">
                    <div class="row">
                        <div class="col-12"><h2><strong>Reporte de validación</strong></h2></div>
                    </div>
                    <div class="row">
                        <div class="col-4"><strong>Versión: </strong></div>
                        <div class="col-8"><span>{version}</span></div>
                    </div>
                    <div class="row">
                        <div class="col-4"><strong>Tipo Comprobante: </strong></div>
                        <div class="col-8"><span>{tipo_comprobante}</span></div>
                    </div>
                    <div class="row">
                        <div class="col-4"><strong>Certificado SAT: </strong></div>
                        <div class="col-8"><span>{certificado_sat}</span></div>
                    </div>
                    <div class="row">
                        <div class="col-4"><strong>Certificado Emisor: </strong></div>
                        <div class="col-8"><span>{certificado_emisor}</span></div>
                    </div>
                    <div class="row">
                        <div class="col-4"><strong>Fecha Emisión: </strong></div>
                        <div class="col-8"><span>{fecha_emision}</span></div>
                    </div>
                    <div class="row">
                        <div class="col-4"><strong>Fecha Certificación: </strong></div>
                        <div class="col-8"><span>{fecha_certificacion}</span></div>
                    </div>
                    <div class="row">
                        <div class="col-4"><strong>UUID: </strong></div>
                        <div class="col-8"><span>{uuid}</span></div>
                    </div>
                    <div class="row">
                        <div class="col-4"><strong>Importe Total: </strong></div>
                        <div class="col-8"><span>{importe_total}</span></div>
                    </div>
                    <div class="row">
                        <div class="col-4"><strong>Importe Subtotal: </strong></div>
                        <div class="col-8"><span>{importe_subtotal}</span></div>
                    </div>                    
                    <div class="row">
                        <div class="col-4"><strong>RFC Emisor: </strong></div>
                        <div class="col-8"><span>{rfc_emisor}</span></div>
                    </div>
                    <div class="row">
                        <div class="col-4"><strong>Nombre Emisor: </strong></div>
                        <div class="col-8"><span>{nombre_emisor}</span></div>
                    </div>
                    <div class="row">
                        <div class="col-4"><strong>RFC Receptor: </strong></div>
                        <div class="col-8"><span>{rfc_receptor}</span></div>
                    </div>
                    <div class="row">
                        <div class="col-4"><strong>Nombre Receptor: </strong></div>
                        <div class="col-8"><span>{nombre_receptor}</span></div>
                    </div>
                </div>
            </div>
        </div>
        <hr />
        """.format(**xml_datas)
        return validar_xml

    def action_validar_facturas(self):
        def _get_attachment_filename(attachment):
            return hasattr(attachment, 'fname') and getattr(attachment, 'fname') or attachment.name
        def _get_attachment_content(attachment):
            return hasattr(attachment, 'content') and getattr(attachment, 'content') or base64.b64decode(attachment.datas).decode("utf-8-sig").encode("utf-8")
        context = dict(self._context)
        for invoice_id in self.env[ context.get('active_model') ].browse( context.get('active_id') ):
            if not invoice_id.is_purchase_document(include_receipts=True):
                return False
            for attachment in self.attachment_ids:
                xmlname = attachment.name.lower()
                if xmlname[-4:] == '.xml':
                    attachment.datas = get_attachment_content(attachment.datas)
                    filename = _get_attachment_filename(attachment)
                    content = _get_attachment_content(attachment)
                    return self.validaxml( invoice_id, content )

    def validaxml_extrainfo(self, invoice_id, tree, vals):
        return vals

    def validaxml(self, invoice_id, cfdi):
        groupModel = self.env['account.tax.group']
        inv_id = self.env['account.move']
        context = dict(self._context)
        tree = fromstring(cfdi)
        Emisor = tree.Emisor
        Receptor = tree.Receptor
        EmisoRfc = Emisor.get('Rfc')
        ReceptorRfc = Receptor.get('Rfc')
        fecha = tree.get('Fecha', '').split('T')
        version = tree.get('Version')
        ns = NS3 if version == '3.3' else NS4
        vals = {
            'codigo': '',
            'estado': '',
            'message_validation_xml': "",
            'reporte_validation_xml': "",
            'act_next': False,
            'errorvalidacion': False
        }
        validar_xml = ''
        EmisorVat = invoice_id.partner_id.vat
        if EmisoRfc != EmisorVat:
            validar_xml += """ <p> El RFC del Emisor %s no coincide con el Proveedor  %s </p>"""%( EmisoRfc,  EmisorVat )
        ReceptorVat = invoice_id.company_id.partner_id.vat
        if ReceptorRfc != ReceptorVat:
            validar_xml += """ <p> El RFC del Receptor %s no coincide con la empresa %s </p>"""%( ReceptorRfc, ReceptorVat )
        tfd = self.l10n_mx_edi_get_tfd_etree(tree)
        uuid = tfd.get('UUID')
        for inv in self.env["account.move"].search([('move_type', 'in', ['out_invoice', 'out_refund', 'in_invoice', 'in_refund']), ('l10n_mx_edi_sat_uuid', '=', uuid)]):    # .filtered(lambda p: p.l10n_mx_edi_cfdi_uuid == uuid):
            vals['uui_duplicado'] = True
            validar_xml += """ <p> UUID Duplicado en Factura : %s </p>"""%( inv.name )
            logging.info('--- UUID Duplicado %s  - %s '%( inv.id, inv.ref )  )
        # Impuestos:
        taxes_groups = {}
        for lines in tree.findall('%sConceptos'%(ns)):
            for line in lines.findall('%sConcepto'%(ns)):
                tax_group = self.get_taxes_ids(line, ns)
                for tax in tax_group:
                    if tax not in taxes_groups:
                        taxes_groups[ tax ] = tax_group[ tax ]
                    else:
                        taxes_groups[ tax ] += tax_group[ tax ]
        # .filtered(lambda l: not l.l10n_mx_edi_imploc):
        for taxg in invoice_id.amount_by_group:
            tax_group_id = taxg[6]
            tax_odoo = taxg[1]
            group_id = groupModel.search_read([('id', '=', tax_group_id)], ['l10n_mx_edi_imploc'])
            if group_id and group_id[0].get('l10n_mx_edi_imploc') == True:
                continue
            tax_xml = taxes_groups.get( tax_group_id, 0.0 )
            if float_compare( abs(tax_odoo), abs(tax_xml), precision_rounding=invoice_id.currency_id.decimal_places ) != 0:
                validar_xml += """ <p> El Impuesto del XML "%s" $ %s no coincide con la Factura: $ %s </p>"""%( taxg[0], tax_xml, tax_odoo )
        SubTotal = float(tree.get('SubTotal', '0.0'))
        if float_compare( invoice_id.l10n_mx_edi_amount_untaxed_wo_discount, SubTotal, precision_rounding=invoice_id.currency_id.decimal_places ) != 0:
            validar_xml += """ <p> El Subtotal del XML $ %s no coincide con la Factura: $ %s </p>"""%( SubTotal, invoice_id.l10n_mx_edi_amount_untaxed_wo_discount )
        Total = float(tree.get('Total', '0.0'))
        if float_compare( invoice_id.amount_total, Total, precision_rounding=invoice_id.currency_id.decimal_places ) != 0:
            validar_xml += """ <p> El Total del XML $ %s no coincide con la Factura : $ %s </p>"""%( Total, invoice_id.amount_total )

        url = 'https://facturacion.finkok.com/servicios/soap/validation.wsdl'
        test = self.company_id.l10n_mx_edi_pac_test_env
        username = self.company_id.l10n_mx_edi_pac_username
        password = self.company_id.l10n_mx_edi_pac_password
        transport = Transport(timeout=20)
        client = Client(url, transport=transport, plugins=[MyLoggingPlugin()])
        contenido = client.service.validate(cfdi, username, password, False)
        logging.info('----- Valida XML %s '%(contenido))
        validateDatas = {}
        if hasattr(contenido, 'error'):
            if contenido.error:
                validar_xml += """ <p> Error al validar XML %s </p>"""%( contenido.error.upper() )
        if not contenido.sat:
            validar_xml += """ <p> No se pudo establecer comunicacion con el SAT. Favor de intentar nuevamente </p>"""
        validateDatas = {
            "xml_valido": contenido.xml,
            "sello_valido": contenido.sello,
            "sello_sat_valido": contenido.sello_sat,
            "estado": str(contenido.sat and contenido.sat.Estado or 'Error SAT'),
            "cod_estatus": str(contenido.sat and contenido.sat.CodigoEstatus or ''),
            "xml_datas": self.get_xml_datas(tree)
        }

        if not validateDatas.get('estado') or validateDatas.get('estado') == 'Error SAT':
            validar_xml += """ <p> No se pudo establecer comunicacion con el SAT. No se puede validar el estado de la factura </p>"""
        invoice_date = fecha and fecha[0] or ''
        vals['estado'] = validateDatas.get('estado')
        vals['codigo'] = validateDatas.get('cod_estatus')
        vals["reporte_validation_xml"] = self._reporte_validacion_xml( validateDatas.get('xml_datas'))
        vals['move_id'] = invoice_id.id
        vals["uuid"] = uuid
        vals['invoice_date'] = invoice_date
        vals["serie"] = tree.get('Serie', '')
        vals["folio"] = tree.get('Folio', '')
        if validar_xml.strip() != "":
            msg = """<div class="card"><div class="card-body">%s</div></div>"""%( validar_xml )
            vals["message_validation_xml"] = msg
            vals['errorvalidacion'] = True
        if vals['estado'] != 'Vigente':
            vals['errorvalidacion'] = True

        extra_vals = self.validaxml_extrainfo( invoice_id, tree, vals )
        vals.update( extra_vals )
        self.write(vals)
        data_obj = self.env['ir.model.data']
        view_name = 'l10n_mx_validatexml.account_invoice_cfdiupload_crear_form'
        view = data_obj.xmlid_to_res_id(view_name)
        return {
            'name': _('Subir XML y PDF'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice.cfdiupload',
            'views': [(view, 'form')],
            'view_id': view,
            'target': 'new',
            'res_id': self.id,
            'context': context,
        }

    def action_create_attachment(self):
        ctx_vals = {
            'check_move_validity': False,
            'check_move_validity': False
        }        
        inv = self.move_id.with_context(**ctx_vals)
        version = '3.3'
        xml_name = '%s %s'%( self.serie, self.folio)
        filename = '%s.xml'%(self.uuid)
        vals = {
            'date': self.invoice_date,
            'invoice_date': self.invoice_date,
            'l10n_mx_edi_sat_uuid': self.uuid
        }
        if len(xml_name.strip()) != 0:
            vals['ref'] = xml_name
            vals['payment_reference'] = xml_name
        inv.write(vals)
        inv._recompute_payment_terms_lines()

        # inv._onchange_invoice_date()
        ctx = self.env.context.copy()
        ctx.pop('default_type', False)
        for attachment in self.attachment_ids:
            xmlname = attachment.name.lower()
            if xmlname[-4:] == '.xml':
                xmlname = '%s.xml'%self.uuid
                cfdi_3_3_edi = self.env.ref('l10n_mx_edi.edi_cfdi_3_3')
                edi_document_vals_list = []
                edi_document_vals_list.append({
                    'edi_format_id': cfdi_3_3_edi.id,
                    'move_id': inv.id,
                    'state': 'sent',
                })
                ediDoc = self.env['account.edi.document'].create(edi_document_vals_list)
                cfdi_filename = '%s.xml'%( self.uuid )
                description = _('Mexican invoice CFDI generated for the %s document.') % inv.name
                cfdi_attachment = cfdi_3_3_edi._create_cfdi_attachment(cfdi_filename, description, inv, attachment.datas)
                ediDoc.attachment_id = cfdi_attachment and cfdi_attachment.id
            if xmlname[-4:] != '.xml':
                filename = attachment.name
                attachment_id = self.env['ir.attachment'].with_context(ctx).create({
                    'name': filename,
                    'res_id': inv.id,
                    'res_model': inv._name,
                    'datas': attachment.datas,
                    'description': 'Mexican invoice ',
                    })
                inv.message_post(
                    body=_(' CFDI Validado '),
                    attachment_ids=[attachment_id.id])

    def get_taxes_ids(self, line, ns):
        taxes_imp = {}
        taxes_ids = []
        indx = 0
        for taxes_line in line.findall('%sImpuestos'%(ns)):
            # Get all taxes
            for taxes in taxes_line.findall('%sTraslados'%(ns)):
                for tras in taxes.findall('%sTraslado'%(ns)):
                    tax_obj = self.env['account.tax']
                    rate = float(tras.get('TasaOCuota')) if tras.get('TasaOCuota') else 0
                    if tras.get('TipoFactor') == 'Tasa':
                        rate = rate * 100
                    rate = round(rate, 4)
                    # ISR
                    if tras.get('Impuesto') == '001':
                        tax_obj = tax_obj.search([
                            ('type_tax_use', '=', 'purchase'),
                            ('amount', '=', rate),
                            ('name', 'like', 'ISR'),
                            ('price_include', '=', False),
                            ('include_base_amount', '=', False),
                            ('tax_group_id.l10n_mx_edi_imploc', '=', False)
                        ], limit=1)
                        if tax_obj:
                            taxes_ids.append(tax_obj.id)
                            taxes_imp[ tax_obj.tax_group_id.id ] = float( tras.get('Importe', '0.0') )
                        else:
                            raise ValidationError(
                                _('The corresponding ISR tax was not found:\n Type: '
                                  'Purchase\n Amount/Percentage: %s') % (str(rate), )
                            )
                    # IVA
                    if tras.get('Impuesto') == '002':
                        tax_obj = tax_obj.search([
                            ('type_tax_use', '=', 'purchase'),
                            ('amount', '=', rate),
                            ('name', 'like', 'IVA'),
                            ('price_include', '=', False),
                            ('include_base_amount', '=', False),
                            ('tax_group_id.l10n_mx_edi_imploc', '=', False)
                        ], limit=1)
                        if tax_obj:
                            taxes_ids.append(tax_obj.id)
                            taxes_imp[ tax_obj.tax_group_id.id ] = float( tras.get('Importe', '0.0') )
                        else:
                            raise ValidationError(
                                _('The corresponding IVA tax was not found:\n Type: '
                                  'Purchase\n Amount/Percentage: %s') % (str(rate), )
                            )
                    # IEPS
                    if tras.get('Impuesto') == '003':
                        tax_obj = tax_obj.search([
                            ('type_tax_use', '=', 'purchase'),
                            ('amount', '=', rate),
                            ('name', 'like', 'IEPS'),
                            ('price_include', '=', False),
                            ('include_base_amount', '=', False),
                            ('tax_group_id.l10n_mx_edi_imploc', '=', False)
                        ], limit=1)
                        if tax_obj:
                            taxes_ids.append(tax_obj.id)
                            taxes_imp[ tax_obj.tax_group_id.id ] = float( tras.get('Importe', '0.0') )
                        else:
                            raise ValidationError(
                                _('The corresponding IEPS tax was not found:\n Type: '
                                  'Purchase\n Amount/Percentage: %s') %
                                (str(rate), )
                            )
            # Get all retentions
            for rets in taxes_line.findall('%sRetenciones'%(ns)):
                for ret in rets.findall('%sRetencion'%(ns)):
                    tax_obj = self.env['account.tax']
                    rate = -1 * float(ret.get('TasaOCuota')) \
                        if ret.get('TasaOCuota') else 0
                    if ret.get('TipoFactor') == 'Tasa':
                        rate = round(rate * 100, 4)
                    # ISR retention
                    if ret.get('Impuesto') == '001':
                        tax_obj = tax_obj.search([
                            ('type_tax_use', '=', 'purchase'),
                            ('amount', '=', rate),
                            ('name', 'like', 'ISR'),
                            ('price_include', '=', False),
                            ('include_base_amount', '=', False),
                            ('tax_group_id.l10n_mx_edi_imploc', '=', False)
                        ], limit=1)
                        if tax_obj:
                            taxes_ids.append(tax_obj.id)
                            taxes_imp[ tax_obj.tax_group_id.id ] = float( ret.get('Importe', '0.0') )
                        else:
                            raise ValidationError(
                                _('The corresponding ISR retention was not found:\n'
                                  ' Type: Purchase\n Amount/Percentage: %s') %
                                (str(rate), )
                            )
                    # IVA retention
                    if ret.get('Impuesto') == '002':
                        tax_obj = tax_obj.search([
                            ('type_tax_use', '=', 'purchase'),
                            ('amount', '=', rate),
                            ('name', 'like', 'IVA'),
                            ('price_include', '=', False),
                            ('include_base_amount', '=', False),
                            ('tax_group_id.l10n_mx_edi_imploc', '=', False)
                        ], limit=1)
                        if tax_obj:
                            taxes_ids.append(tax_obj.id)
                            taxes_imp[ tax_obj.tax_group_id.id ] = float( ret.get('Importe', '0.0') )
                        else:
                            raise ValidationError(
                                _('The corresponding IVA retention was not found:\n'
                                  ' Type: Purchases\n Amount/Percentage: %s') %
                                (str(rate), )
                            )
                    # IEPS retention
                    if ret.get('Impuesto') == '003':
                        tax_obj = tax_obj.search([
                            ('type_tax_use', '=', 'purchase'),
                            ('amount', '=', rate),
                            ('name', 'like', 'IEPS'),
                            ('price_include', '=', False),
                            ('include_base_amount', '=', False),
                            ('tax_group_id.l10n_mx_edi_imploc', '=', False)
                        ], limit=1)
                        if tax_obj:
                            taxes_ids.append(tax_obj.id)
                            taxes_imp[ tax_obj.tax_group_id.id ] = float( ret.get('Importe', '0.0') )
                        else:
                            raise ValidationError(
                                _('The corresponding IEPS retention was not '
                                  'found:\n Type: Purchases\n '
                                  'Amount/Percentage: %s') % (str(rate), )
                            )
            
        return taxes_imp

"""
Borrar XML Adjunto
AttachModel = env['ir.attachment']
for rec in records:
    if rec.is_purchase_document(include_receipts=True):
        attach_id = AttachModel.search([('res_model', '=', 'account.move'), ('res_id', '=', rec.id), ('name', '=', '%s.xml'%(rec.l10n_mx_edi_cfdi_uuid) )])
        if rec.edi_document_ids:
            rec.edi_document_ids.unlink()
        attach_id.unlink()



Actualizar UUID
inv_ids = env['account.move'].search([('move_type', 'in', ['out_invoice', 'out_refund', 'in_invoice', 'in_refund']), ('l10n_mx_edi_sat_uuid', '=', False)], limit=3000)
for inv in inv_ids:
    inv['l10n_mx_edi_sat_uuid'] = inv.l10n_mx_edi_cfdi_uuid
"""

