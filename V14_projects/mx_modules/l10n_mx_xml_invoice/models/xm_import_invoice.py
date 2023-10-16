# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from odoo import api, models, fields, tools, _
from odoo.exceptions import UserError, ValidationError

import requests
import base64
from lxml import etree
from lxml import objectify
from lxml.objectify import fromstring
from cfdiclient import Validacion
from datetime import datetime
from datetime import date
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)

class CreateInvoiceXml(models.Model):
    _name = 'xml.import.invoice'
    _description = "CreateInvoiceXml: Create purchase invoice from XML file."
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string="Name",
        required=True,
        index=True,
        copy=False,
        default='New',
        readonly=True,
    )
    state = fields.Selection(
        string="State",
        selection=[
            ('import', 'Import XML'),
            ('validate', 'All XML are valid'),
            ('invoiced', 'Invoices created'),
            ('error', 'With errors'),
        ],
        required=False,
        default='import',
    )
    xml_table_ids = fields.One2many(
        comodel_name='xml.table.invoice',
        inverse_name='xml_wiz_id',
    )
    # xml_ok = fields.Boolean(
    #     string="Is all xml OK?",
    #     default=False,
    # )
    journal_id = fields.Many2one(
        comodel_name='account.journal',
        string="Journal",
        default=lambda self: self.env['account.journal'].search([
            ('type', '=', 'purchase'),
            ('company_id', '=', self.env.user.company_id.id)
        ], limit=1),
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    account_id = fields.Many2one(
        comodel_name='account.account',
        string="Account for invoice line",
    )
    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Analytic Account',
    )
    analytic_tag_ids = fields.Many2many(
        comodel_name='account.analytic.tag',
        string='Analytic Tags',
    )
    invoice_ids = fields.One2many(
        comodel_name="account.move",
        inverse_name="xml_import_id",
        string="Invoices",
        required=False,
    )
    invoice_count = fields.Integer(
        string='Invoice Count',
        compute='_compute_onchange_xml_table_ids',
        readonly=True,
    )


    def action_view_invoice(self):
        invoices = self.mapped('invoice_ids')
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [
                    (state, view) for state, view in action['views'] if view != 'form'
                ]
            else:
                action['views'] = form_view
            action['res_id'] = invoices.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        return action

    @api.onchange('xml_table_ids')
    def _compute_onchange_xml_table_ids(self):
        for xml in self:
            list_invoice_ids = []
            state = 'validate'
            for table in xml.xml_table_ids:
                if table.move_id:
                    list_invoice_ids.append(table.move_id.id)
                if table.status != "Comprobante obtenido satisfactoriamente.":
                    state = 'error'

            xml.invoice_ids = list_invoice_ids
            xml.invoice_count = len(xml.invoice_ids)
            if xml.invoice_count == 0 \
                    and state != 'error' \
                    and len(xml.xml_table_ids) == 0:
                state = 'import'
            if len(xml.invoice_ids) > 0 and state != 'error':
                state = 'invoiced'
            xml.write({
                'state': state
            })

    def unlink(self):
        for xml_import in self:
            if len(xml_import.xml_table_ids) != 0:
                raise UserError(_(
                    'You cannot delete this record as it has registered lines'))
        return super(CreateInvoiceXml, self).unlink()

    def action_import_xml_invoices(self):
        return {
            'name': _('Import xml'),
            'res_model': 'xml.import.wizard',
            'view_mode': 'form',
            'context': {'default_xml_import_invoice_id': self.id},
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    @api.onchange('journal_id')
    def onchange_journal(self):
        for rec in self:
            rec.account_id = rec.journal_id.default_account_id

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'xml.import.invoice') or 'New'
        return super(CreateInvoiceXml, self).create(vals)

    def _l10n_mx_edi_get_sat_status(self, supplier_rfc, customer_rfc, total, uuid):
        url = 'https://consultaqr.facturaelectronica.sat.gob.mx/ConsultaCFDIService.svc?wsdl'
        headers = {'SOAPAction': 'http://tempuri.org/IConsultaCFDIService/Consulta', 'Content-Type': 'text/xml; charset=utf-8'}
        template = """<?xml version="1.0" encoding="UTF-8"?>
        <SOAP-ENV:Envelope xmlns:ns0="http://tempuri.org/" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
           <SOAP-ENV:Header/>
           <ns1:Body>
              <ns0:Consulta>
                 <ns0:expresionImpresa>${data}</ns0:expresionImpresa>
              </ns0:Consulta>
           </ns1:Body>
        </SOAP-ENV:Envelope>"""
        namespace = {'a': 'http://schemas.datacontract.org/2004/07/Sat.Cfdi.Negocio.ConsultaCfdi.Servicio'}
        params = '?re=%s&amp;rr=%s&amp;tt=%s&amp;id=%s' % (
            tools.html_escape(supplier_rfc or ''),
            tools.html_escape(customer_rfc or ''),
            total or 0.0, uuid or '')
        soap_env = template.format(data=params)
        #An exception might be raised here and should be managed by the calling function
        soap_xml = requests.post(url, data=soap_env, headers=headers, timeout=20)
        response = fromstring(soap_xml.text)
        fetched_status = response.xpath('//a:Estado', namespaces=namespace)
        status = fetched_status[0] if fetched_status else ''
        return status        

    def validate_xml(self):
        def _get_attachment_content(attachment):
            cfdi = base64.b64decode(attachment)
            return fromstring(cfdi)

        # xml_ok = True
        for table in self.xml_table_ids:
            tree = _get_attachment_content(table.xml)
            state = 'validate'
            if self._get_stamp_data(tree) is None:
                table.status = _('Error in XML file')
                state = 'error'
            else:
                tfd = self._get_stamp_data(tree)
                xmluuid = str(tfd.get('UUID'))
                table.uuid = xmluuid

                validacion = Validacion()
                rfc_emisor = tree.Emisor.get('Rfc')
                rfc_receptor = tree.Receptor.get('Rfc')
                total = tree.get('Total')
                uuid = tfd.get('UUID')

                resss = self._l10n_mx_edi_get_sat_status(rfc_receptor, rfc_emisor, total, uuid)
                print('--- resssresss', resss)

                sat_state = validacion.obtener_estado(
                    rfc_emisor,
                    rfc_receptor,
                    total,
                    uuid,
                )
                print('--- sat_state', sat_state, rfc_emisor, rfc_receptor, total, uuid)
                table.status = sat_state['codigo_estatus'][4:]
                if table.status != "Comprobante obtenido satisfactoriamente.":
                    state = 'error'
                if self.company_id.vat != rfc_receptor:
                    table.status = _("This XML does not belong to this company.")
                    state = 'error'


            # self.xml_ok = xml_ok
            self.write({
                'state': state,
            })

    def get_customer_for_general_public(self):
        partner_obj = self.env['res.partner']
        partner_id = partner_obj.search([('name', '=', 'ClientePrueba')], limit=1)
        if not partner_id:
            raise UserError(_('Please create a customer named Test Client.'))

        return partner_id

    def create_xml_invoice(self):
        inv_id = self.env['account.move']

        def _get_attachment_content(attachment):
            cfdi = base64.b64decode(attachment)
            return fromstring(cfdi)

        for rec in self:
            creates_partners = []
            products_not_found = []
            for xml in rec.xml_table_ids:
                if not xml.move_id:
                    tree = _get_attachment_content(xml.xml)
                    currency = self.get_currency(tree.get('Moneda'))
                    partner = self.get_partner(
                        tree.Emisor.get('Rfc'),
                        tree.Emisor.get('Nombre'),
                    )
                    partner_id = partner.get('partner_obj')
                    if partner.get('create_partner'):
                        creates_partners.append(partner_id)
                    invoice_lines = []
                    invoice_product_not_found = []
                    for lines in tree.findall('{http://www.sat.gob.mx/cfd/3}Conceptos'):
                        for line in lines.findall(
                                '{http://www.sat.gob.mx/cfd/3}Concepto'):
                            taxes_ids = [(6, 0, self.get_taxes_ids(line))]
                            product = self.get_product(
                                partner_id,
                                line.get('Descripcion'),
                                line.get('NoIdentificacion'),
                            )
                            if not product:
                                invoice_product_not_found.append({
                                    'description': line.get('Descripcion'),
                                    'id': line.get('NoIdentificacion'),
                                })
                            product_uom = self.get_uom(line.get('ClaveUnidad'), product)
                            account = self.get_account(product, self.account_id)
                            discount = self.get_discount(line)
                            # TODO: revisar otras formas de buscar cuentas analiticas
                            analytic_account = self.analytic_account_id
                            analytic_tags = [(6, 0, self.analytic_tag_ids._ids)]
                            vals = {
                                'product_id': product.id or False,
                                'name': line.get('Descripcion'),
                                'quantity': float(line.get('Cantidad')),
                                'product_uom_id': product_uom.id or False,
                                'tax_ids': taxes_ids,
                                'price_unit': float(line.get('ValorUnitario')),
                                'discount': discount,
                                'account_id': account.id,
                                'analytic_account_id': analytic_account.id or False,
                                'analytic_tag_ids': analytic_tags,
                            }
                            invoice_lines.append(vals)
                    xml_name = '%s-%s'%( tree.get('Serie', ''), tree.get('Folio', '') )
                  
                    _logger.info('--------- UUID %s - Folio %s '%(xml.uuid, xml_name) )
                    # 'xml_file': xml.xml,
                    fecha = tree.get('Fecha', '').split('T')
                    invoice_date = fecha and fecha[0] or ''
                    anterior = inv_id.get_mes_anterior()
                    actual = inv_id.get_mes_actual()
                    hoy = date.today()
                    fecha = datetime.strptime( invoice_date, '%Y-%m-%d' ).date()
                    if self.user_has_groups('account.group_account_invoice'):
                        if fecha >= anterior and fecha <= actual:
                            invoice_date = hoy

                    valsMove = {
                        'partner_id': partner_id.id,
                        'journal_id': self.journal_id.id,
                        'date': invoice_date,
                        'invoice_date': invoice_date,
                        'ref': xml_name,
                        'move_type': 'in_invoice',
                        'invoice_line_ids': invoice_lines,
                        'xml_filename': '%s.xml'%(xml.uuid),
                        'company_id': self.company_id.id,
                        'currency_id': currency.id,
                    }
                    if len(xml_name.strip()) != 0:
                        valsMove['ref'] = xml_name
                        valsMove['payment_reference'] = xml_name
                    account_move = self.env['account.move'].create(valsMove)
                    # -- Proceso guardar EDI Documents
                    cfdi_3_3_edi = self.env.ref('l10n_mx_edi.edi_cfdi_3_3')
                    edi_document_vals_list = []
                    edi_document_vals_list.append({
                        'edi_format_id': cfdi_3_3_edi.id,
                        'move_id': account_move.id,
                        'state': 'sent',
                    })
                    ediDoc = self.env['account.edi.document'].create(edi_document_vals_list)
                    cfdi_filename = '%s.xml'%( xml.uuid )
                    description = _('Mexican invoice CFDI generated for the %s document.') % account_move.name
                    cfdi_attachment = cfdi_3_3_edi._create_cfdi_attachment(cfdi_filename, description, account_move, xml.xml)
                    ediDoc.attachment_id = cfdi_attachment and cfdi_attachment.id

                    xml.move_id = account_move.id
                    if len(invoice_product_not_found) != 0:
                        products_not_found.append({
                            'move_obj': account_move,
                            'products': invoice_product_not_found,
                        })
                    message = "<ul>%s" % (_('CFDI generated by XML validation:'))
                    message += "<ul><li>UUID: %s </li></ul>"%( xml.uuid )
                    message += "</ul>"
                    account_move.message_post(body=message)
            self.write({
                'state': 'invoiced',
            })
            if len(creates_partners) != 0:
                message = "<ul>%s" % (_('A new partner was created:'))
                for partner in creates_partners:
                    message += "<ul><li><a target='_blank' href='%s'>%s</a></li>" % (
                        '/web#id=%s&view_type=form&model=res.partner' % (
                            partner.id,
                        ),
                        partner.name,
                    )
                    message += "</ul>"
                message += "</ul>"
                self.message_post(body=message)
            if len(products_not_found) != 0:
                message = "<ul>%s" % (
                    _('Products not found in the following invoices:'))
                for move in products_not_found:
                    message += "<ul><li><a target='_blank' href='%s'>%s</a></li>" % (
                        '/web#id=%s&view_type=form&model=account.move' % (
                            move.get('move_obj').id,
                        ),
                        move.get('move_obj').ref,
                    )
                    for product in move.get('products'):
                        message += "<ul><li>ID: %s - Description: %s</li></ul>" % \
                                   (product.get('id'), product.get('description'))
                    message += "</ul>"
                message += "</ul>"
                self.message_post(body=message)

    @api.model
    def _get_stamp_data(self, cfdi):
        self.ensure_one()
        if not hasattr(cfdi, 'Complemento'):
            return None
        attribute = 'tfd:TimbreFiscalDigital[1]'
        namespace = {'tfd': 'http://www.sat.gob.mx/TimbreFiscalDigital'}
        node = cfdi.Complemento.xpath(attribute, namespaces=namespace)
        return node[0] if node else None

    def get_taxes_ids(self, line):
        taxes_ids = []
        for taxes_line in line.findall('{http://www.sat.gob.mx/cfd/3}Impuestos'):
            # Get all taxes
            for taxes in taxes_line.findall('{http://www.sat.gob.mx/cfd/3}Traslados'):
                for tax in taxes.findall('{http://www.sat.gob.mx/cfd/3}Traslado'):
                    tax_obj = self.env['account.tax']
                    rate = float(tax.get('TasaOCuota')) if tax.get('TasaOCuota') else 0
                    if tax.get('TipoFactor') == 'Tasa':
                        rate = rate * 100
                    rate = round(rate, 4)
                    # ISR
                    if tax.get('Impuesto') == '001':
                        tax_obj = tax_obj.search([
                            ('type_tax_use', '=', 'purchase'),
                            ('amount', '=', rate),
                            ('name', 'like', 'ISR'),
                            ('price_include', '=', False),
                            ('include_base_amount', '=', False),
                        ], limit=1)
                        if tax_obj:
                            taxes_ids.append(tax_obj.id)
                        else:
                            raise ValidationError(
                                _('The corresponding ISR tax was not found:\n Type: '
                                  'Purchase\n Amount/Percentage: %s') % (str(rate), )
                            )
                    # IVA
                    if tax.get('Impuesto') == '002':
                        tax_obj = tax_obj.search([
                            ('type_tax_use', '=', 'purchase'),
                            ('amount', '=', rate),
                            ('name', 'like', 'IVA'),
                            ('price_include', '=', False),
                            ('include_base_amount', '=', False)],
                            limit=1)

                        if tax_obj:
                            taxes_ids.append(tax_obj.id)
                        else:
                            raise ValidationError(
                                _('The corresponding IVA tax was not found:\n Type: '
                                  'Purchase\n Amount/Percentage: %s') % (str(rate), )
                            )
                    # IEPS
                    if tax.get('Impuesto') == '003':
                        tax_obj = tax_obj.search([
                            ('type_tax_use', '=', 'purchase'),
                            ('amount', '=', rate),
                            ('name', 'like', 'IEPS'),
                            ('price_include', '=', False),
                            ('include_base_amount', '=', False)
                        ], limit=1)
                        if tax_obj:
                            taxes_ids.append(tax_obj.id)
                        else:
                            raise ValidationError(
                                _('The corresponding IEPS tax was not found:\n Type: '
                                  'Purchase\n Amount/Percentage: %s') %
                                (str(rate), )
                            )
                # Get all retentions
                for rets in taxes_line.findall(
                        '{http://www.sat.gob.mx/cfd/3}Retenciones'):
                    for ret in rets.findall('{http://www.sat.gob.mx/cfd/3}Retencion'):
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
                                ('include_base_amount', '=', False)
                            ], limit=1)
                            if tax_obj:
                                taxes_ids.append(tax_obj.id)
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
                                ('include_base_amount', '=', False)
                            ], limit=1)
                            if tax_obj:
                                taxes_ids.append(tax_obj.id)
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
                                ('include_base_amount', '=', False)
                            ], limit=1)
                            if tax_obj:
                                taxes_ids.append(tax_obj.id)
                            else:
                                raise ValidationError(
                                    _('The corresponding IEPS retention was not '
                                      'found:\n Type: Purchases\n '
                                      'Amount/Percentage: %s') % (str(rate), )
                                )
        return taxes_ids

    def get_partner(self, RFC, name):
        partner_obj = self.env['res.partner']
        partner_obj = partner_obj.search([('vat', '=', RFC)], limit=1)
        create_partner = False
        if not partner_obj:
            vals = {
                'name': name,
                'vat': RFC,
                'company_type': 'company',
                'type': 'contact'
            }
            partner_obj = partner_obj.create(vals)
            create_partner = True

        return {
            'partner_obj': partner_obj,
            'create_partner': create_partner,
        }

    def get_currency(self, name):
        if name == 'XXX':
            name = 'MXN'
        currency_obj = self.env['res.currency'].search([
            ('name', '=', str(name)),
            ('active', '=', True),
        ])
        if not currency_obj:
            raise ValidationError(
                _('There is no currency named %s: Please check your settings or contact'
                  ' an administrator.') % (str(name))
            )
        return currency_obj

    def get_product(self, partner_id, description, code):
        operator = 'ilike'
        product_obj = self.env['product.product']
        _logger.info(' ------------ Proveedor %s Prod %s - Cod %s  '%(partner_id.name, description, code) )
        suppliers = self.env['product.supplierinfo'].search([
            ('name', '=', partner_id.id ),
            '|',
            ('product_code', operator, code),
            ('product_name', operator, description)])
        _logger.info('------------- Product suppliers 01 %s'%(suppliers) )
        if suppliers:
            product_obj = self.env['product.product'].search([('product_tmpl_id.seller_ids', 'in', suppliers.ids)], limit=1)
            _logger.info('------------- Product suppliers 02 %s'%(product_obj) )
        else:
            if code:
                product_obj = product_obj.search([('barcode', '=', code)], limit=1)
            if not product_obj and code:
                product_obj = product_obj.search([('default_code', '=', code)], limit=1)
            if not product_obj and description:
                product_obj = product_obj.search([('name', '=', description)], limit=1)
        return product_obj

    def get_uom(self, code, product):
        # TODO: Falta como buscar la unidad de medida por medio del codigo del codigo
        #  del sat
        uom_obj = self.env['uom.uom']
        if code:
            uom_obj = uom_obj.search([('name', '=', code)])
        if product and not uom_obj:
            uom_obj = product.uom_po_id
        return uom_obj

    def get_account(self, product, account_obj):
        if product:
            account_obj = product.product_tmpl_id.get_product_accounts(False)['expense']
        return account_obj

    def get_discount(self, line):
        discount = 0
        if line.get('Descuento'):
            discount_amount = float(line.get('Descuento')) * 100
            total_amount = float(line.get('Importe'))
            discount = discount_amount / total_amount
        return discount


class WizardTableXml(models.Model):
    _name = "xml.table.invoice"
    _description = "XML  Table Invoice"

    name = fields.Char(
        string="Name XML",
    )
    xml = fields.Binary(
        string="XML", attachment=True
    )
    uuid = fields.Char(
        string="UUID",
    )
    status = fields.Char(
        string="Status",
    )
    move_id = fields.Many2one(
        comodel_name='account.move',
        string="Invoice",
    )
    xml_wiz_id = fields.Many2one(
        comodel_name='xml.import.invoice',
    )

    def unlink(self):
        for table in self:
            if table.move_id:
                raise UserError(
                    _('You cannot delete this record as you have an invoice created'))
        return super(WizardTableXml, self).unlink()

