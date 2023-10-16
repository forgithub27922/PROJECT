demo.py


# controllers/main.py
class PosWsYeidala(http.Controller):

    @http.route('/web/refund', type='http', auth="none", csrf=False)
    def refund(self, login=None, password=None, *kw):
        ensure_db()
        values =  {}
        values = self.action_authenticate(request.params['login'], request.params['password'])
        if 'error' in values:
            return self.returnResponse(values)
        data = dict( request.params )
        posConfig = request.env['pos.config'].sudo()
        values = posConfig.action_process_refund(data={
            'NumeroOrden': data.get('NumeroOrden', ''),
            'IdEmpresa': data.get('IdEmpresa', ''),
            'TipoCancelacion': data.get('TipoCancelacion', '')
        })
        return self.returnResponse(values)


    @http.route('/web/posorderOLD', type='http', auth="none", csrf=False)
    def posorderold(self, login=None, password=None, *kw):
        ensure_db()
        values = self.action_authenticate(request.params['login'], request.params['password'])
        if 'error' in values:
            return self.returnResponse(values)
        raw_body_data = http.request.httprequest.data or "{}"
        json_datas = json.loads( raw_body_data)
        _logger.info('--- DATAS POST %s '%(json_datas) )
        if not json_datas:
            values['error'] = 'Los valores del JSON estan vacios'
            return self.returnResponse(values)
        dbname = request.session.db
        registry = odoo.modules.registry.Registry(dbname)
        with registry.cursor() as cr:
            posConfig = request.env['pos.config'].sudo()
            company_id = request.env.ref('__export__.res_company_12_276637f1', raise_if_not_found=False)
            values = posConfig.action_process_posns(data=json_datas)
            request.env['res.users.log'].sudo()._gc_user_logs()
        return self.returnResponse(values)


# models/point_of_sale.py
class PosSession(models.Model):
    _inherit = 'pos.config'

    def action_process_posns(self, data={}):
        paymentMethod = self.env['pos.payment.method'].sudo()
        accountTax = self.env['account.tax'].sudo()
        posOrder = self.env['pos.order'].sudo()
        resPartner = self.env['res.partner'].sudo()
        productProduct = self.env['product.product'].sudo()
        orderChannel = self.env['pos.order.channel'].sudo()

        user_timezone = pytz.timezone(self._context.get('tz') or self.env.user.tz or 'UTC')
        timezone = pytz.timezone('UTC')

        empresa_id = data.get('IdEmpresa')
        config_id = self.search([('empresans_id', '=', empresa_id)])
        if not config_id:
            return {'error': 'No existe la sucursal'}
        # Inicia session: 
        if not config_id.current_session_id:
            config_id.open_session_cb_ns()
        if not config_id.current_session_id:
            return {'error': 'No tiene una sesion abierta'}
        # inicia proceso
        session_id = config_id.current_session_id
        session_id.login()
        error = 0
        ventas = data.get('Ventas') or []
        for venta in ventas:
            fecha = venta.get('FechaVenta', '').replace('T', ' ')
            creation_date = utc_converter(self, fecha)
            channel_id = orderChannel.search(['|', ('code', '=', venta.get('Area')),  ('name', '=', venta.get('Area'))])
            noorderns = '%s_%s'%( empresa_id, venta.get('NumeroOrden') )
            order_id = posOrder.search([('noorderns', '=', noorderns)])
            if order_id:
                return {'error': 'Ya existe una venta con este numero de orden: [%s] %s - %s'%( venta.get('Area'), empresa_id, venta.get('NumeroOrden') ) }            

            partner_id = resPartner.search([('ref', '=', venta.get('IdCliente', ''))], limit=1)
            uuid = data.get('uuid') or posOrder.generate_unique_id(session_id)
            order = {
                'id': uuid, 
                'data': {
                    'pos_session_id': session_id.id,
                    'pricelist_id': config_id.pricelist_id.id,
                    'partner_id': partner_id and partner_id.id or False,
                    'user_id': self.env.uid,
                    'uid': uuid,
                    'sequence_number': session_id.sequence_number,
                    'creation_date': '%s'%creation_date,
                    'fiscal_position_id': False,
                    'server_id': False,
                    'to_invoice': False,
                    'is_tipped': False,
                    'tip_amount': 0,
                    'loyalty_points': 0,
                    'name': 'Orden %s'%( uuid ) , 
                    'amount_paid':  venta.get('Total') or 0.0, 
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
                    return {'error': 'No se encuentra el producto %s'%(concepto.get('IdProducto'))}
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
                            return {'error': 'No existe el Impuesto %s - %s'%( imp.get('Impuesto'), imp.get('Tasa') ) }
                        tax_ids.append(tax_id.id)
                    if imp.get('Impuesto') == 'IEPS':
                        tax_id = accountTax.search([
                            ('company_id', '=', config_id.company_id.id),
                            ('type_tax_use', '=', 'sale'),
                            ('amount', '=', rate),
                            ('name', 'like', 'IEPS')
                        ], limit=1)
                        if not tax_id:
                            return {'error': 'No existe el Impuesto %s - %s'%( imp.get('Impuesto'), imp.get('Tasa') ) }
                        tax_ids.append(tax_id.id)
                descuento = concepto.get('Descuento') or 0.0
                sinimp = concepto.get('ImporteSinImpuestos') or 0.0
                line_tmp = {
                    'qty': concepto.get('Cantidad', 0.0), 
                    'price_unit': concepto.get('PrecioUnitario', 0.0), 
                    'price_subtotal': concepto.get('ImporteSinImpuestos', 0.0), 
                    'price_subtotal_incl': price_subtotal_incl, 
                    'discount': descuento * 100 / sinimp  if sinimp != 0.0 else 0.0 , 
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
                forma_pago = pago.get('FormaPago') if pago.get('FormaPago', '')  != 'Plataforma' else channel_id.name
                if forma_pago == 'Plataforma':
                    pago['FormaPago'] = channel_id and channel_id.name or ''
                payment_id = paymentMethod.search([('name', '=', forma_pago), ('company_id', '=', config_id.company_id.id)])
                if not payment_id:
                    return {'error': 'No existe la Forma de Pago %s '%( forma_pago ) }
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
                noorderns = noorderns,
                channel_id = channel_id and channel_id.id or False
            ).create_from_ui([order], draft=False)
            _logger.info('------- order_ids %s '%order_ids )
        if error:
            return {'error': 'No se pudo procesar las ventas'}
        if not order_ids:
            try:
                session_id.action_pos_session_closing_control()
            except Exception as e:
                _logger.info('------- POS_NS Error clossing  %s '%(str(e)) )
                pass
            return {'error': 'No se pudo procesar la Venta'}
        return {'mensaje': 'Datos procesados correctamente'}


    def action_process_refund(self, data={}):
        posOrder = self.env['pos.order'].sudo()
        empresa_id = data.get('IdEmpresa')
        config_id = self.search([('empresans_id', '=', empresa_id)])
        if not config_id:
            return {'error': 'No existe la sucursal'}
        # Inicia session: 
        if not config_id.current_session_id:
            config_id.open_session_cb_ns()
        if not config_id.current_session_id:
            return {'error': 'No tiene una sesion abierta'}
        noorderns = '%s_%s'%( empresa_id, data.get('NumeroOrden') )
        order_id = posOrder.search([('noorderns', '=', noorderns), ('name', 'not ilike', 'REFUND')])
        if not order_id:
            return {'error': 'No existe la venta'}
        if order_id.state == 'draft':
            return {'error': 'No se puede procesar la devolucion'}
        res = order_id.with_context(wsns=True, tipo=data.get('TipoCancelacion')).refund()
        # if data.get('TipoCancelacion') == 'devolucion':
        return {'mensaje': 'Cancelacion procesado correctamente'}

