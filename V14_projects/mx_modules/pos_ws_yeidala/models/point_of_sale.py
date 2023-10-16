# -*- coding: utf-8 -*-

import pytz
from datetime import timezone, datetime, timedelta
import datetime
import json

import logging
from odoo import models, fields, api, _
from odoo import api, fields, models, tools, _
from odoo.tools import float_is_zero, float_round
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


def utc_converter(self, dt):
    #################################xxxx##########################
    # [CALL FROM action_process_posns]
    fmt = '%Y-%m-%d %H:%M:%S %Z%z'
    dt1 = datetime.datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
    user_tz = pytz.timezone(self._context.get('tz') or self.env.user.tz or 'UTC')
    utc_tz = pytz.timezone('UTC')
    ist_local = user_tz.localize(dt1)
    return ist_local.astimezone(utc_tz)


class AccountMove(models.Model):
    _name = 'pos.order.nationalsoft'
    _description = "Pos Order National Soft"
    _order = 'order_to_process desc, state'

    POS_SESSION_STATE = [
        ('draft', 'New'),
        ('verify', 'Verify'),
        ('cancel', 'Cancelled'),
        ('paid', 'Paid'),
        ('done', 'Posted'),
        ('invoiced', 'Invoiced'),
        ('refunded', 'Refunded'),
        ('error', 'Errors')
    ]

    ws_status = fields.Selection(
        selection=[
            ('to_send', 'To Send'),
            ('sent', 'Sent'),
            ('to_cancel', 'To Cancel'),
            ('cancelled', 'Cancelled')
        ],
        string='WS status', copy=False)
    ws_error = fields.Char(copy=False)
    ws_content = fields.Text(string='Raw Body Json',
                             required=True, copy=False)
    date_order = fields.Datetime(string='Date',
                                 readonly=True, index=True,
                                 default=fields.Datetime.now)

    name = fields.Char('ID Empresa')
    noorden = fields.Char('Numero Orden')
    nointentos = fields.Integer('Numero de Intentos', default=1)
    order_to_process = fields.Boolean(default=True)
    config_id = fields.Many2one(
        'pos.config', string='Point of Sale',
        help="The physical point of sale you will use.",
        required=True, index=True)
    order_id = fields.Many2one(
        'pos.order', string='POS Order',
        required=False, index=True)

    is_refund = fields.Boolean(default=False)
    refund_id = fields.Many2one(
        'pos.order', string='Refund Order',
        required=False, index=True)
    tipocancelacion = fields.Selection([
        ('devolucion', 'Devolucion'),
        ('merma', 'Merma')
    ], string="Tipo Cancelacion", default='')

    state = fields.Selection(
        POS_SESSION_STATE, string='Status',
        required=True, readonly=True,
        index=True, copy=False, default='draft')
    user_id = fields.Many2one(
        'res.users', string='Opened By',
        required=True, index=True, readonly=True,
        default=lambda self: self.env.uid,
        ondelete='restrict')
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        readonly=True, default=lambda self: self.env.company)

    # -------------------------------------------------------------------------
    # BUTTONS METHODS
    # -------------------------------------------------------------------------
    def ws_action_clear_error(self):
        #################################xxxx##########################
        for record in self:
            record.ws_error = False

    # -------------------------------------------------------------------------
    # BASE METHODS
    # -------------------------------------------------------------------------
    def action_process_posns(self, datas={}, login=""):
        print("action_process_posns CALLED:::::::::::>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>.")
        #################XXXXXXXXXXXXXXXXXXXXXXXXX##################
        # call from  controller : posorder , demo.py
        error = 0
        posOrder = self.env['pos.order'].sudo()
        resPartner = self.env['res.partner'].sudo()
        orderChannel = self.env['pos.order.channel'].sudo()

        res = {}
        # if not datas:
        #     error = 1
        #     return {'error': 'NS: Los valores del JSON estan vacios'}

        resUsers = self.env['res.users']
        company_id = self.env.ref('__export__.res_company_12_276637f1', raise_if_not_found=False)
        user_ids = resUsers.search_read([('login', '=', login)], ['name'], limit=1)
        user_id = user_ids and user_ids[0] or {}
        print("USER ID:::::::::>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", user_id)
        # if not user_id:
        #     error = 1
        #     return {'error': 'NS: No existe el usuario del POS'}

        posConfig = self.env['pos.config'].sudo().with_company(company_id)
        nationalSoft = self.env['pos.order.nationalsoft'].with_company(company_id).with_user(user_id)
        productProduct = self.env['product.product'].sudo().with_company(company_id)
        accountTax = self.env['account.tax'].sudo().with_company(company_id)
        paymentMethod = self.env['pos.payment.method'].sudo().with_company(company_id)

        empresa_id = datas.get('IdEmpresa')
        print(empresa_id)
        ventas = datas.get('Ventas') or []
        config_id = posConfig.search([('empresans_id', '=', empresa_id)])
        print("config:::::::::::::::::::::::::::::::::::::::", config_id)
        for venta in ventas:
            fecha = venta.get('FechaVenta', '').replace('T', ' ')
            creation_date = utc_converter(self, fecha)

            # - Busca la Sucursal
            noorderns = venta.get('NumeroOrden')
            config_id = posConfig.search([('empresans_id', '=', empresa_id)])
            print("config:::::::::::::::::::::::::::::::::::::::",config_id)
            if not config_id:
                error = 1
                return {'error': 'NS: No existe la sucursal "%s" Venta: %s  ' % (empresa_id, noorderns)}

            # - Busca la Orden de Venta de NS
            order_id = self.search([('name', '=', empresa_id.strip()), ('noorden', '=', noorderns)])
            if order_id:
                vals = {'nointentos': order_id.nointentos + 1}
                if order_id.state == 'draft':
                    vals['ws_content'] = json.dumps(datas)
                order_id.write(vals)
                error = 1
                return {'error': 'NS: Ya existe una venta con este numero de orden: [%s] %s ' % (empresa_id, noorderns)}

            noorder = '%s_%s' % (empresa_id, noorderns)
            order_id = posOrder.search([('noorderns', '=', noorder)])
            if order_id:
                error = 1
                return {'error': 'NS: Ya existe una venta con este numero de orden: [%s] %s ' % (empresa_id, noorderns)}

            # - Busca productos
            conceptos = venta.get('Conceptos') or []
            for concepto in conceptos:
                product_id = productProduct.search([('default_code', '=', concepto.get('IdProducto'))])
                if not product_id:
                    error = 1
                    return {'error': 'NS: No existe el producto %s ' % (concepto.get('IdProducto'))}

                # - Busca Impuestos
                for imp in concepto.get('Impuestos', []):
                    rate = imp.get('Tasa')
                    rate = round(rate * 100, 4)
                    if imp.get('Impuesto') == 'IVA':
                        tax_id = accountTax.search([
                            ('company_id', '=', config_id.company_id.id),
                            ('type_tax_use', '=', 'sale'),
                            ('amount', '=', rate),
                            ('name', 'like', 'IVA'),
                            ('price_include', '=', False),
                            ('include_base_amount', '=', False)],
                            limit=1)
                        if not tax_id:
                            error = 1
                            return {
                                'error': 'NS: No existe el Impuesto %s - %s' % (imp.get('Impuesto'), imp.get('Tasa'))}
                    elif imp.get('Impuesto') == 'IEPS':
                        tax_id = accountTax.search([
                            ('company_id', '=', config_id.company_id.id),
                            ('type_tax_use', '=', 'sale'),
                            ('amount', '=', rate),
                            ('name', 'like', 'IEPS')
                        ], limit=1)
                        if not tax_id:
                            error = 1
                            return {
                                'error': 'NS: No existe el Impuesto %s - %s' % (imp.get('Impuesto'), imp.get('Tasa'))}
                    else:
                        error = 1
                        return {'error': 'NS: No existe el Impuesto %s - %s' % (imp.get('Impuesto'), imp.get('Tasa'))}

            # - Busca FormadePagos
            for pago in venta.get('Pagos'):
                forma_pago = pago.get('FormaPago')
                payment_id = paymentMethod.search(
                    [('name', '=', forma_pago), ('company_id', '=', config_id.company_id.id)])
                if not payment_id:
                    error = 1
                    return {'error': 'NS: No existe la Forma de Pago %s ' % (forma_pago)}

            vals = {
                'ws_status': 'to_send',
                'name': empresa_id or '',
                'noorden': noorderns or '',
                'date_order': str(creation_date).replace('T', ' ')[:19],
                'ws_content': json.dumps(datas),
                'config_id': config_id and config_id.id or False,
                'state': 'draft',
                'user_id': user_id['id'],
                'company_id': company_id.id,
            }
            wsns_id = nationalSoft.create(vals)
            if wsns_id:
                return {'mensaje': 'El pedido se creo de manera asincrona'}
            else:
                return {'error': 'NS: El pedido se creo de manera asincrona'}
        return res

    # ----------------------
    # CRON Process Done
    # ----------------------
    def action_process_done(self, with_commit=None):
        ####################XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX#########
        # call from _process_documents_web_services
        # <button name = "action_process_done" [BTN CMTD]

        paymentMethod = self.env['pos.payment.method'].sudo()
        accountTax = self.env['account.tax'].sudo()
        posOrder = self.env['pos.order'].sudo()
        resPartner = self.env['res.partner'].sudo()
        productProduct = self.env['product.product'].sudo()
        orderChannel = self.env['pos.order.channel'].sudo()
        for rec in self:
            config_id = rec.config_id
            # Inicia session: 
            if not config_id.current_session_id:
                config_id.open_session_cb_ns()
            if not config_id.current_session_id:
                return {'error': 'No tiene una sesion abierta'}

            # inicia proceso
            session_id = config_id.current_session_id
            session_id.login()
            error = 0
            print("\n\nRECORD:>>>>>>>>>", rec)
            data = json.loads(rec.ws_content)
            print(data)
            ventas = data.get('Ventas') or []
            for venta in ventas:
                creation_date = rec.date_order

                channel_id = orderChannel.search(
                    ['|', ('code', '=', venta.get('Area')), ('name', '=', venta.get('Area'))])
                noorderns = '%s_%s' % (rec.name, rec.noorden)
                order_id = posOrder.search([('noorderns', '=', noorderns)])
                if order_id:
                    error = 1
                    rec.write({
                        'state': 'error',
                        'ws_error': 'Ya existe una venta con este numero de orden: [%s] %s - %s' % (
                            venta.get('Area'), rec.name, rec.noorden)
                    })
                    break

                partner_id = resPartner.search([('ref', '=', venta.get('IdCliente', ''))], limit=1)
                uuid = data.get('uuid') or posOrder.generate_unique_id(session_id)
                order = {
                    'id': uuid,
                    'data': {
                        'pos_session_id': session_id.id,
                        'pricelist_id': config_id.pricelist_id.id,
                        'partner_id': partner_id and partner_id.id or False,
                        'user_id': rec.user_id and rec.user_id.id or False,
                        'uid': uuid,
                        'sequence_number': session_id.sequence_number,
                        'creation_date': '%s' % creation_date,
                        'fiscal_position_id': False,
                        'server_id': False,
                        'to_invoice': False,
                        'is_tipped': False,
                        'tip_amount': 0,
                        'loyalty_points': 0,
                        'name': 'Orden %s' % (uuid),
                        'amount_paid': venta.get('Total') or 0.0,
                        'amount_total': venta.get('Total') or 0.0,
                        'amount_tax': 0,
                        'amount_return': 0,
                        'lines': [],
                        'statement_ids': [],
                    }
                }
                amount_tax = 0.0
                lines = []
                conceptos = venta.get('Conceptos') or []
                for concepto in conceptos:
                    product_id = productProduct.search([('default_code', '=', concepto.get('IdProducto'))])
                    if not product_id:
                        error = 1
                        rec.write({
                            'state': 'error',
                            'ws_error': 'No se encuentra el producto %s' % (concepto.get('IdProducto'))
                        })
                        break
                    tax_ids = []
                    price_subtotal_incl = concepto.get('Cantidad') * concepto.get('PrecioUnitario')
                    for imp in concepto.get('Impuestos', []):
                        rate = imp.get('Tasa')
                        rate = rate * 100
                        rate = round(rate, 4)
                        amount_tax += imp.get('Importe') or 0.0
                        if imp.get('Impuesto') == 'IVA':
                            tax_id = accountTax.search([
                                ('company_id', '=', config_id.company_id.id),
                                ('type_tax_use', '=', 'sale'),
                                ('amount', '=', rate),
                                ('name', 'like', 'IVA'),
                                ('price_include', '=', False),
                                ('include_base_amount', '=', False)],
                                limit=1)
                            if not tax_id:
                                error = 1
                                rec.write({
                                    'state': 'error',
                                    'ws_error': 'No existe el Impuesto %s - %s' % (imp.get('Impuesto'), imp.get('Tasa'))
                                })
                                break
                            tax_ids.append(tax_id.id)
                        if imp.get('Impuesto') == 'IEPS':
                            tax_id = accountTax.search([
                                ('company_id', '=', config_id.company_id.id),
                                ('type_tax_use', '=', 'sale'),
                                ('amount', '=', rate),
                                ('name', 'like', 'IEPS')
                            ], limit=1)
                            if not tax_id:
                                error = 1
                                rec.write({
                                    'state': 'error',
                                    'ws_error': 'No existe el Impuesto %s - %s' % (imp.get('Impuesto'), imp.get('Tasa'))
                                })
                                break

                            tax_ids.append(tax_id.id)
                    if error == 1:
                        break

                    descuento = concepto.get('Descuento') or 0.0
                    sinimp = concepto.get('ImporteSinImpuestos') or 0.0
                    line_tmp = {
                        'qty': concepto.get('Cantidad', 0.0),
                        'price_unit': concepto.get('PrecioUnitario', 0.0),
                        'price_subtotal': concepto.get('ImporteSinImpuestos', 0.0),
                        'price_subtotal_incl': price_subtotal_incl,
                        'discount': descuento * 100 / sinimp if sinimp != 0.0 else 0.0,
                        'product_id': product_id.id,
                        'tax_ids': [[6, False, tax_ids]],
                        'pack_lot_ids': [],
                        'description': concepto.get('Descripcion', ''),
                        'full_product_name': product_id.display_name,
                        'price_extra': 0
                    }
                    lines.append([
                        0, 0, line_tmp
                    ])

                order['data']['lines'] = lines
                # Agrega Impuestos
                if amount_tax:
                    order['data']['amount_tax'] = amount_tax
                tip_amount = 0.0
                statement_ids = []

                for pago in venta.get('Pagos'):
                    forma_pago = pago.get('FormaPago') if pago.get('FormaPago', '') != 'Plataforma' else channel_id.name
                    if forma_pago == 'Plataforma':
                        pago['FormaPago'] = channel_id and channel_id.name or ''
                    payment_id = paymentMethod.search(
                        [('name', '=', forma_pago), ('company_id', '=', config_id.company_id.id)])
                    if not payment_id:
                        error = 1
                        rec.write({
                            'state': 'error',
                            'ws_error': 'No existe la Forma de Pago %s ' % (forma_pago)
                        })
                        break

                    statement_tmp = {
                        'name': venta.get('FechaVenta', '').replace('T', ' ') or fields.Datetime.now(),
                        'payment_method_id': payment_id.id,
                        'amount': pago.get('Importe', 0.0),
                        'payment_status': 'DONE',
                        'ticket': '',
                        'card_type': '',
                        'cardholder_name': '',
                        'transaction_id': '',
                        'is_change': True
                    }
                    statement_ids.append([
                        0, 0, statement_tmp
                    ])
                    if pago.get('Propina') != 0.0:
                        tip_amount += pago['Propina']
                        tip_tmp = {
                            'name': venta.get('FechaVenta', '').replace('T', ' ') or fields.Datetime.now(),
                            'payment_method_id': payment_id.id,
                            'amount': pago.get('Propina', 0.0),
                            'payment_status': 'DONE',
                            'ticket': '',
                            'card_type': '',
                            'cardholder_name': '',
                            'transaction_id': '',
                            'is_tipped': True
                        }
                        statement_ids.append([
                            0, 0, tip_tmp
                        ])

                order['data']['statement_ids'] = statement_ids
                if tip_amount:
                    order['data']['is_tipped'] = True
                    order['data']['tip_amount'] = tip_amount
                    order['data']['amount_paid'] += tip_amount
                    order['data']['amount_total'] += tip_amount
                    tip_dict = {
                        'qty': 1,
                        'price_unit': tip_amount,
                        'price_subtotal': tip_amount,
                        'price_subtotal_incl': tip_amount,
                        'discount': 0,
                        'product_id': config_id.tip_product_id and config_id.tip_product_id.id or False,
                        'tax_ids': [[6, False, []]],
                        'pack_lot_ids': [],
                        'description': '',
                        'full_product_name': 'Propinas',
                        'price_extra': 0
                    }
                    order['data']['lines'].append([
                        0, 0, tip_dict
                    ])
                order_ids = posOrder.with_context(
                    nationalsoft=rec.id,
                    noorderns=noorderns,
                    channel_id=channel_id and channel_id.id or False
                ).create_from_ui([order], draft=False)
                _logger.info('------- order_ids %s ' % order_ids)

            if error == 1:
                continue

            if with_commit:
                self.env.cr.commit()

            if rec.order_id:
                rec.write({
                    'order_to_process': False,
                    'state': 'done'
                })

        return True

    def _process_documents_web_services(self, job_count=None, with_commit=True):
        ###########XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX#################################
        # call from _cron_process_generate_pos_nationalsoft

        print("method called _process_documents_web_services")
        all_jobs = self.filtered(lambda p: p.order_to_process == True and p.state in ['draft', 'verify'])
        jobs_to_process = all_jobs[0:job_count] if job_count else all_jobs
        for documents in jobs_to_process:
            try:
                with self.env.cr.savepoint(flush=False):
                    self._cr.execute('SELECT * FROM pos_order_nationalsoft WHERE id IN %s FOR UPDATE NOWAIT',
                                     [tuple(documents.ids)])

            except OperationalError as e:
                if e.pgcode == '55P03':
                    _logger.debug('Another transaction already locked documents rows. Cannot process payslip.')
                    if not with_commit:
                        raise UserError(_('This payslip is being sent by another process already. '))
                    continue
                else:
                    raise e

            documents.action_process_done(with_commit=True)
            if with_commit and len(jobs_to_process) > 0:
                # documents.write({'order_to_process': False})
                self.env.cr.commit()
        return len(all_jobs) - len(jobs_to_process)

    def _cron_process_generate_pos_nationalsoft(self, job_count=None):
        #########XXXXXXXXXXXXXXXXXXXXXXXXXXXX#################################
        # call from ir.cron [can't get the JS DATA]

        print("method called")
        pos_documents = self.search([('state', 'in', ('draft', 'verify')), ('order_to_process', '=', True)],
                                    limit=job_count)
        nb_remaining_jobs = pos_documents._process_documents_web_services(job_count=job_count)
        # if nb_remaining_jobs > 0:
        #     self.env.ref('pos_ws_yeidala.ir_cron_generate_pos_nationalsoft').method_direct_trigger()

    # ------------------------
    # WS DEVOLUCIONES
    # ------------------------
    def action_process_refund(self, datas={}):
        ############XXXXXXXXXXXXXXXXXXX################################
        # call from refund controller , demo.py

        posOrder = self.env['pos.order'].sudo()
        ConfigModel = self.env['pos.config'].sudo()

        tipocancelacion = datas.get('TipoCancelacion') or ''
        empresa_id = datas.get('IdEmpresa') or ''
        noorden = datas.get('NumeroOrden') or ''
        config_id = ConfigModel.search([('empresans_id', '=', empresa_id)])
        if not config_id:
            return {'error': 'No existe la sucursal'}

        noorderns = '%s_%s' % (empresa_id, noorden)
        order_id = posOrder.search([('noorderns', '=', noorderns), ('name', 'not ilike', 'REFUND')])
        if not order_id:
            return {'error': 'No existe la venta'}

        ns_id = self.search([('name', '=', empresa_id), ('noorden', '=', noorden)])
        if not ns_id:
            return {'error': 'No existe la Venta'}

        if ns_id.is_refund and ns_id.refund_id:
            return {'error': 'La devolucion ya fue procesada de manera asincrona'}

        ns_id.write({'is_refund': True, 'tipocancelacion': tipocancelacion})
        return {'mensaje': 'La devolucion se creo de manera asincrona'}

    # ----------------------
    # CRON Process Refund
    # ----------------------
    def action_process_refund_pos(self, with_commit=None):
        #############XXXXXXXXXXXX#######################################
        # call from _process_refund_documents_web_services

        ConfigModel = self.env['pos.config'].sudo()
        posOrder = self.env['pos.order'].sudo()
        for rec in self:
            config_id = ConfigModel.search([('empresans_id', '=', rec.name)])
            if not config_id.current_session_id:
                config_id.open_session_cb_ns()
            rec.order_id.sudo().with_context(wsns=True, tipo=rec.tipocancelacion, nationalsoft_refund=rec.id).refund()

    def _process_refund_documents_web_services(self, job_count=None, with_commit=True):

        ######XXXXXXXXXXXXXXXX##############################################################
        # call from _cron_process_generate_refund_nationalsoft

        all_jobs = self.filtered(lambda p: p.state in [
            'done'] and p.is_refund == True and p.order_id and not p.refund_id)  # and p.refund_id == None
        jobs_to_process = all_jobs[0:job_count] if job_count else all_jobs
        for documents in jobs_to_process:
            try:
                with self.env.cr.savepoint(flush=False):
                    self._cr.execute('SELECT * FROM pos_order_nationalsoft WHERE id IN %s FOR UPDATE NOWAIT',
                                     [tuple(documents.ids)])

            except OperationalError as e:
                if e.pgcode == '55P03':
                    _logger.debug('Another transaction already locked documents rows. Cannot process refund NS.')
                    if not with_commit:
                        raise UserError(_('This refund NS is being sent by another process already. '))
                    continue
                else:
                    raise e

            documents.action_process_refund_pos(with_commit=True)
            if with_commit and len(jobs_to_process) > 0:
                self.env.cr.commit()
        return len(all_jobs) - len(jobs_to_process)

    def _cron_process_generate_refund_nationalsoft(self, job_count=None):
        # FROM CRON
        ###XXXXXXXXXXXXXXXXXXXXXXXXXXX##########################
        pos_documents = self.search(
            [('state', 'in', ['done']), ('is_refund', '=', True), ('refund_id', '=', False), ('order_id', '!=', False)],
            limit=job_count)
        nb_remaining_jobs = pos_documents._process_refund_documents_web_services(job_count=job_count)


class AccountMove(models.Model):
    _name = 'pos.order.channel'
    _description = "Pos Order Channel"

    name = fields.Char('Name')
    code = fields.Char('Code')
    company_id = fields.Many2one(
        'res.company', string='Company', required=True, readonly=True,
        default=lambda self: self.env.company)


class PosPayment(models.Model):
    _inherit = "pos.payment"

    is_tipped = fields.Boolean('Is it tipped?', readonly=True)


class PosOrder(models.Model):
    _inherit = "pos.order"

    noorderns = fields.Char(string='No Orden NS')
    channel_id = fields.Many2one(
        'pos.order.channel', string='Order Channel',
        change_default=True, index=True,
        states={'draft': [('readonly', False)], 'paid': [('readonly', False)]})

    @api.model
    def create(self, values):
        print("\n\n::::::::::::::::::::::::::::::::>>>METHOD CALLED")
        session = self.env['pos.session'].browse(values['session_id'])
        values['noorderns'] = self._context.get('noorderns')
        values['channel_id'] = self._context.get('channel_id')
        orders = super(PosOrder, self).create(values)
        session.login_sequence_number()
        print('------------- sesion', self._context)

        # context from action_process_done
        nationalsoft_id = self._context.get('nationalsoft')

        if nationalsoft_id:
            for order in orders:
                nationaSoftModel = self.env['pos.order.nationalsoft'].sudo()
                nationaSoftModel.browse(nationalsoft_id).write({
                    'order_id': order.id
                })

        # context from action_process_refund
        nationalsoft_refund = self._context.get('nationalsoft_refund')

        if nationalsoft_refund:
            for order in orders:
                nationaSoftModel = self.env['pos.order.nationalsoft'].sudo()
                nationaSoftModel.browse(nationalsoft_refund).write({
                    'refund_id': order.id
                })

        return orders

    @api.model
    def _payment_fields(self, order, ui_paymentline):
        res = super()._payment_fields(order, ui_paymentline)
        print("\n\n RES::::::::::>>>>>>>>>>>>", res)
        print("PAYMENT LINE::::::>>>>>>>>>>>>>.", ui_paymentline)
        res.update({
            'is_tipped': ui_paymentline.get('is_tipped')
        })
        print("IS TIPPED::::::>>>>>>>>>>>>>>>>>>>>>>", res)
        return res

    def generate_unique_id(self, session_id=False):
        #####XXXXXXXXXXXXXXXX CALL FROM action_process_done XXXXXXX####################
        # Generates a public identification number for the order.
        # The generated number must be unique and sequential. They are made 12 digit long
        # to fit into EAN-13 barcodes, should it be needed
        ssid = session_id or self.session_id.id or False
        s_id = '%s' % ssid.id or 0
        l_no = '%s' % ssid.login_number or 0
        s_no = '%s' % (ssid.sequence_number)
        res = '%s-%s-%s' % (
            s_id.rjust(5, '0'),
            l_no.rjust(3, '0'),
            s_no.rjust(4, '0')
        )
        return res

    def _prepare_refund_values(self, current_session):
        self.ensure_one()
        res = super(PosOrder, self)._prepare_refund_values(current_session)
        print("BEFORE X RES::::::::::>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", res)
        res.update({
            'noorderns': self.noorderns,
            'channel_id': self.channel_id and self.channel_id.id or False
        })
        print("AFTER X RES::::::::::>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", res)
        return res

    def refund(self):
        """Create a copy of order  for refund order"""
        ctx = self.env.context
        refundModel = self.env['pos.order']
        scrapModel = self.env['stock.scrap']
        nsModel = self.env['pos.order.nationalsoft']

        for order in self:
            if refundModel.search([('pos_reference', '=', order.pos_reference), ('noorderns', '=', order.noorderns),
                                   ('id', '!=', order.id)], count=True):
                print("UNDER IFF:::::>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                msg = 'Existe una devolucion para esta orden de venta %s' % (order.noorderns)
                if 'wsns' in ctx:
                    return {'error': msg}
                else:
                    raise UserError(msg)
        res = super().refund()
        if 'res_id' in res:
            for order in self:
                refund_id = refundModel.browse(res.get('res_id'))
                refund_id.noorderns = order.noorderns
                if refund_id.state == 'draft':
                    for payment_id in order.payment_ids:
                        line_return_id = payment_id.copy({
                            'pos_order_id': refund_id.id,
                            'name': payment_id.name,
                            'amount': payment_id.amount * -1,
                            'payment_method_id': payment_id.payment_method_id.id,
                            'payment_date': payment_id.payment_date
                        })
                order._compute_batch_amount_all()
                refund_id._compute_batch_amount_all()
                if refund_id._is_pos_order_paid():
                    print("IM IN IF::::::::::::::::::::::::::>>>>>>>>>>>>>>>REFUNDDDDDDDDDDDDDDDDDDDDDDDDDDD")
                    refund_id.action_pos_order_paid()
                    refund_id._create_order_picking()
                if ctx.get('tipo', '') == 'merma':
                    picking_type = order.picking_type_id
                    if picking_type.return_picking_type_id:
                        return_picking_type = picking_type.return_picking_type_id
                        return_location_id = return_picking_type.default_location_dest_id.id
                    else:
                        return_picking_type = picking_type
                        return_location_id = picking_type.default_location_src_id.id
                    for refund_line in refund_id.lines:
                        if refund_line.product_id.type == 'product':
                            crap_id = scrapModel.create({
                                'product_id': refund_line.product_id.id,
                                'scrap_qty': abs(refund_line.qty),
                                'product_uom_id': refund_line.product_uom_id.id,
                                'location_id': return_location_id,
                                'origin': refund_id.name
                            })
                            try:
                                crap_id.action_validate()
                            except:
                                pass
        return res

    def _create_order_picking(self):
        print("METHOD CALLEDDDDDDDD::::::<<<<<<<<<<<<<<>>>>>>PICKING")
        self.ensure_one()
        print(self.date_order)
        return super(PosOrder,
                     self.with_context(force_period_date=self.date_order, force_pos_order=True))._create_order_picking()


class PosConfig(models.Model):
    _inherit = 'pos.config'

    empresans_id = fields.Char(string='IdEmpresa NS')

    def open_session_cb_ns(self, check_coa=True):
        # call from action_process_done

        self.ensure_one()
        if not self.current_session_id:
            self._check_pricelists()
            self._check_company_journal()
            self._check_company_invoice_journal()
            self._check_company_payment()
            self._check_currencies()
            self._check_profit_loss_cash_journal()
            self._check_payment_method_ids()
            # self._check_payment_method_receivable_accounts()
            self.env['pos.session'].create({
                'user_id': self.env.uid,
                'config_id': self.id
            })
        return {
        }


class PosSession(models.Model):
    _inherit = 'pos.session'

    # def _create_account_move(self, balancing_account=False, amount_to_balance=0, bank_payment_method_diffs=None):
    #     # DONE
    #     print("CONTEXT FROM SESSION:::::>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", self._context)
    #     print("\n\n\nFROM PROJECT:::::>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    #     print("force_period_date<><><><><>><><><><>", self._context.get('force_period_date'))
    #     print("force_pos_order<><><><><>><><><><>", self._context.get('force_pos_order'))
    #     res = super()._create_account_move(balancing_account, amount_to_balance, bank_payment_method_diffs)
    #     account_analytic_id = self.config_id.picking_type_id.warehouse_id.account_analytic_id
    #     print("config_id:>>>>>>>>>>>>>>>>>>>>>>>>", self.config_id)
    #     print("ACCOUNT:>>>>>>>>>>>>>>>>>>>>>>>>", account_analytic_id)
    #     print("\n\nMOVE ID::::>>>>>>>>>>>>>>>>>>>>>>>>>>", self.move_id)
    #     for line in self.move_id.line_ids:
    #         line.write({
    #             'analytic_account_id': account_analytic_id and account_analytic_id.id or False
    #         })
    #     return res

    def login_sequence_number(self):
        # DONE
        self.ensure_one()
        sequence_number = self.sequence_number + 1
        print("\n\n SEQ NUMBER::::::>>>>>>>>>>>>>>>>>>>>", sequence_number)
        self.write({
            'sequence_number': sequence_number,
        })
        print(sequence_number)
        return sequence_number

    # def _create_picking_at_end_of_session(self):
    #     date_order_f = False
    #     for rec in self.order_ids:
    #         date_order_f = rec.date_order
    #         break
    #     return super(PosSession, self.with_context(force_period_date=date_order_f,
    #                                                force_pos_order=True))._create_picking_at_end_of_session()


class StockMove(models.Model):
    _inherit = "stock.move"

    def write(self, vals):
        print("\n\nCALLED FROM STOCK MOVEEEEEEEEEE::::::::::::>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        force_period_date = self._context.get('force_period_date', False)
        # print("\n\n\nforce_period_date::::::::::::::::", force_period_date)
        force_pos_order = self._context.get('force_pos_order', False)
        # print("force_pos_order:::::::::::::::::::", force_pos_order)
        if force_period_date and force_pos_order:
            if 'date' in vals:
                vals['date'] = force_period_date
            if vals.get('state') == 'done' and 'date' in vals:
                vals['date'] = force_period_date
                vals['create_date'] = force_period_date
        res = super(StockMove, self).write(vals)
        return res


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def write(self, vals):
        print("::::::<<<<<<<<<<<<<<stock.move.line>>>>>>>>>>>::::::::::::::::::::::::")
        force_period_date = self._context.get('force_period_date', False)
        force_pos_order = self._context.get('force_pos_order', False)
        if force_period_date and force_pos_order:
            if 'date' in vals:
                vals['date'] = force_period_date
            if vals.get('state') == 'done':
                vals['date'] = force_period_date
                vals['create_date'] = force_period_date
        res = super(StockMoveLine, self).write(vals)
        return res


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # @api.model
    # def _create_picking_from_pos_order_lines(self, location_dest_id, lines, picking_type, partner=False):
    #     return super(PosSession, self.with_context(force_period_date=rec.date_order,
    # #                                                    force_pos_order=True))
    # @api.model_create_multi
    # def create(self, vals_list):
    #     print("CONTEXT:::><<<<<<<<<<<<<<<<<<<<<DDDDDDDDDDDDDDDDDDDD>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>.", self._context)
    #     print(s)
    #     return super(StockPicking, self).create(vals_list)

    def _prepare_picking_vals(self, partner, picking_type, location_id, location_dest_id):
        print("CONTEXT SESSION [STOCK.PICKING]:::>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>", self._context)
        print("\n\n\n<<<<<<:::::::::::::::METHOD CALLED WHEN CLOSE THE SESSION [STOCK.PICKING]::::>>>>>>>>>>>")
        res = super(StockPicking, self)._prepare_picking_vals(partner, picking_type, location_id, location_dest_id)
        force_period_date = self._context.get('force_period_date', False)
        print("force_period_date[[STOCK.PICKING] _prepare_picking_vals]", force_period_date)
        force_pos_order = self._context.get('force_pos_order', False)
        print("force_pos_order[[STOCK.PICKING] _prepare_picking_vals]", force_pos_order)
        if force_period_date and force_pos_order:
            res['date_done'] = force_period_date
            res['scheduled_date'] = force_period_date
            res['create_date'] = force_period_date
        print("NOT IN IF [STOCK.picking]")
        return res

    def _prepare_stock_move_vals(self, first_line, order_lines):
        print("::::::<<<<<<<<<<<<<FROM[STOCK.PICKING]::::>>>>>>>>>>>")
        res = super(StockPicking, self)._prepare_stock_move_vals(first_line, order_lines)
        force_period_date = self._context.get('force_period_date', False)
        print("force_period_date[[STOCK.PICKING]_prepare_stock_move_vals]", force_period_date)
        force_pos_order = self._context.get('force_pos_order', False)
        print("force_period_date[[STOCK.PICKING]_prepare_stock_move_vals]", force_period_date)
        if force_period_date and force_pos_order:
            print("UNDER IF [STOCK.picking] _prepare_stock_move_vals")
            res['date'] = force_period_date
            res['create_date'] = force_period_date
        print("NOT IN IF [STOCK.picking]")
        return res

    def write(self, vals):
        print("WRITE STOCK.PICKING")
        print("::::::<<<<<<<<<<<<<FROM[STOCK.PICKING]::::>>>>>>>>>>>")
        force_period_date = self._context.get('force_period_date', False)
        print("force_period_date[[STOCK.PICKING] write]", force_period_date)
        force_pos_order = self._context.get('force_pos_order', False)
        print("force_period_date[[STOCK.PICKING] write]", force_period_date)
        if force_period_date and force_pos_order:
            print("UNDER IF [STOCK.picking] _prepare_picking_vals")
            if 'date_done' in vals:
                print('date_done')
                vals['date_done'] = force_period_date
        res = super(StockPicking, self).write(vals)
        print("NOT IN IF [STOCK.picking]")
        return res


class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'

    @api.model
    def create(self, vals):
        print("<<<<<<<<<<<<::::::::::::::::::::::::::stock.valuation.layer::::>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        force_period_date = self._context.get('force_period_date', False)
        force_pos_order = self._context.get('force_pos_order', False)
        if force_period_date and force_pos_order:
            print("UNDER IF [stock.valuation.layer] create")
            vals['create_date'] = force_period_date
        res = super(StockValuationLayer, self).create(vals)
        for v in res:
            if v.create_date != force_period_date:
                v['create_date'] = force_period_date
        return res

    def write(self, vals):
        print("<<<<<<<<<<<<::::::::::::::::::::::::::stock.valuation.layer::::>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        force_period_date = self._context.get('force_period_date', False)
        force_pos_order = self._context.get('force_pos_order', False)
        if force_period_date and force_pos_order:
            vals['create_date'] = force_period_date
        res = super(StockValuationLayer, self).write(vals)
        return res
