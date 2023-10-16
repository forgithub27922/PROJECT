# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
import pytz

class wizard_factura_global(models.TransientModel):
    _name = 'wizard.factura.global'

    def _get_journal_pedidos_domain(self):
        domain=[('type','=','sale'),('company_id', '=', self.env.company.id)]
        return domain 
    def _get_partner_domain(self):
        domain=[('company_id', '=', self.env.company.id),('vat','=','XAXX010101000')]
        return domain 

    def _get_invoice_product_domain(self):
        domain=['|',('company_id','=',False),('company_id', '=', self.env.company.id),('f_global','=',True)]
        return domain 

    def _get_analytic_account_domain(self):
        domain=['|',('company_id','=',False),('company_id', '=', self.env.company.id)]
        return domain 



    def _get_pedidos_pos_domain_init(self):
        domain=[('id','in',self.pos_order_list.ids)]
        return domain 



    @api.depends('partner_to_group','fecha_inicial','fecha_final','journal_pedidos')
    def _get_pedidos_pos_domain(self):
        # by default timezone = UTC
        user_time_zone = pytz.UTC
        if self.env.user.partner_id.tz :
            # change the timezone to the timezone of the user
            user_time_zone = pytz.timezone(self.env.user.partner_id.tz)
        self.fecha_inicial= self.fecha_inicial or str(datetime.today()-relativedelta(days=1))
        self.fecha_final= self.fecha_final or str(datetime.today())
        if self.fecha_inicial > self.fecha_final:
            f_limite_superior=fields.Datetime.from_string(self.fecha_inicial)+relativedelta(hours=23,minutes=59,seconds=59)
            f_limite_inferior=fields.Datetime.from_string(self.fecha_final)
        else:
            f_limite_superior=fields.Datetime.from_string(self.fecha_final)+relativedelta(hours=23,minutes=59,seconds=59)
            f_limite_inferior=fields.Datetime.from_string(self.fecha_inicial)
        f_limite_superior=fields.Datetime.to_string(user_time_zone.localize(f_limite_superior).astimezone(pytz.UTC))  
        f_limite_inferior=fields.Datetime.to_string(user_time_zone.localize(f_limite_inferior).astimezone(pytz.UTC))  
        pos_order_ids=[]
        self.pedidos_pos = False
        if self.partner_to_group:
            pos_orders=self.env['pos.order'].search([('amount_total','>',0.0),('account_move','=',False),('partner_id','=',self.partner_to_group.id),('state','not in',['cancel','draft']),('sale_journal','=',self.journal_pedidos.id),('date_order','>=',f_limite_inferior),('date_order','<=',f_limite_superior)])
        else :
            pos_orders=self.env['pos.order'].search([('amount_total','>',0.0),('account_move','=',False),('state','not in',['cancel','draft']),('sale_journal','=',self.journal_pedidos.id),('date_order','>=',f_limite_inferior),('date_order','<=',f_limite_superior)])
        if pos_orders :
            remove_orders=self.env['pos.order']
            for order in pos_orders:
                returned_orders = self.env['pos.order'].search([('amount_total','<',0),('pos_reference','=',order.pos_reference)])
                if returned_orders:
                    sum_amount = sum([order.amount_total for order in returned_orders])
                    if (order.amount_total + sum_amount ) <= 0.0 :
                        remove_orders = remove_orders + order
            pos_orders = pos_orders - remove_orders          
            self.pos_order_list= [(6,0,pos_orders.ids )]
        else:
            if self.pos_order_list.ids:
                self.pos_order_list= [(5)]
            if self.pedidos_pos.ids:
                self.pedidos_pos = [(5)]
    
        return 


    journal_pedidos=fields.Many2one('account.journal', string='Journal de pedidos', domain=_get_journal_pedidos_domain)
    partner_to_group=fields.Many2one('res.partner', string='Cliente a agrupar', domain=_get_partner_domain)
    invoice_partner=fields.Many2one('res.partner', string='Cliente que aparece en la factura', required=True, domain=_get_partner_domain)
    fecha_inicial=fields.Date('Fecha Inicial', default=str(datetime.today()-relativedelta(days=1)))        
    fecha_final=fields.Date('Fecha Final', default=str(datetime.today()))        
    pedidos_pos=fields.Many2many('pos.order','pedidos_pos_rel','pos_id','pedidos_pos_id', required=True, domain=_get_pedidos_pos_domain_init)        
    devoluciones_pos=fields.Many2many('pos.order','devoluciones_pos_rel','pos_id','devoluciones_pos_id')        
    invoice_product=fields.Many2one('product.product', string='Producto que aparece en la factura', required=True, domain=_get_invoice_product_domain)        
    pos_order_list = fields.Many2many('pos.order', 'pos_order_rel', 'wizard_id', 'pos_order_id', compute=_get_pedidos_pos_domain) 

    analytic_account_id = fields.Many2one ('account.analytic.account', domain=_get_analytic_account_domain) 


    def _update_devoluciones_pos(self):
        for record in self:
            devoluciones= self.env['pos.order']
            for pedido in record.pedidos_pos:
                returned_orders = self.env['pos.order'].search([('amount_total','<',0),('pos_reference','=',pedido.pos_reference)])
                devoluciones = devoluciones + returned_orders
            record.devoluciones_pos = [(6,0, devoluciones.ids)]
  

    
    @api.onchange('fecha_final','fecha_inicial')
    def check_fechas(self):

        if self.fecha_inicial > self.fecha_final:
            return{
                  'warning':{'title':_('Fechas desordenadas'),'message':_("La fecha inicial es mayor que la final")}
                  }

        return 
  
    def crear_factura(self):
    #Este loop revisa que los pedidos solo tengan un impuesto para la factura global por producto
        metodos_pago={}
        self._update_devoluciones_pos() 
        for pedido in self.pedidos_pos+ self.devoluciones_pos:
            for payment in pedido.payment_ids:
                if not payment.payment_method_id.l10n_mx_edi_payment_method_id.id in metodos_pago.keys():
                    metodos_pago[payment.payment_method_id.l10n_mx_edi_payment_method_id.id]= payment.amount
                else:
                    metodos_pago[payment.payment_method_id.l10n_mx_edi_payment_method_id.id]+=payment.amount   
            for line in pedido.lines:
                product_taxes_ids = [tax for tax in line.product_id.taxes_id if tax.company_id.id == line.order_id.company_id.id ]
                cuenta=0
                for tax in product_taxes_ids:
                    if tax.f_global:
                        cuenta+=1
                if cuenta > 1 :
                    raise except_orm('Error','El pedido %s contiene el product : %s con mas de un impuesto para generar la factura global' %(pedido.name,line.product_id.name))

                    

        invoice_obj=self.env['account.move']
        acc = self.invoice_partner.property_account_receivable_id.id
        inv = {
            'f_global': True,
            'invoice_origin': 'Ordenes del Pos',
            'journal_id': self.journal_pedidos.id or None,
            'move_type': 'out_invoice',
            'partner_id': self.invoice_partner.id,
            'narration': 'Factura del %s al %s' %(self.fecha_inicial, self.fecha_final),
            }
        #inv.update(invoice_obj.onchange_partner_id('out_invoice', self.invoice_partner.id)['value'])
        max_metodo_pago=max(metodos_pago, key=lambda k: metodos_pago[k])
        inv['l10n_mx_edi_payment_method_id']=max_metodo_pago or None
        inv['l10n_mx_edi_usage']='P01'
#Este loop genera un arreglo con las lineas por tipo de impuesto
        inv['invoice_line_ids']=[]
        for pedido in self.pedidos_pos: 
            detalle_impuestos={} 
            for line in pedido.lines:
                taxes=line.tax_ids_after_fiscal_position.ids
                tax_key='0'
                for tax in taxes:
                    if tax_key=='0': 
                        tax_key+=str(tax)
                    else:
                        tax_key+= ","+str(tax)
                if  tax_key in detalle_impuestos.keys():
                    detalle_impuestos[tax_key] += line.tax_ids_after_fiscal_position and line.tax_ids_after_fiscal_position[0].price_include and line.price_subtotal_incl or line.price_subtotal
                else:
                    detalle_impuestos[tax_key]  = line.tax_ids_after_fiscal_position and line.tax_ids_after_fiscal_position[0].price_include and line.price_subtotal_incl or line.price_subtotal


            '''
            Check if pedido has devoluciones
            '''
            devoluciones=self.devoluciones_pos.filtered(lambda order: order.pos_reference == pedido.pos_reference)
            if devoluciones:
                '''
                Actualizar detalle_impuestos
                '''
                for devolucion in devoluciones: 
                    for line in devolucion.lines:
                        taxes=line.tax_ids_after_fiscal_position.ids
                        tax_key='0'
                        for tax in taxes:
                            if tax_key=='0': 
                                tax_key+=str(tax)
                            else:
                                tax_key+= ","+str(tax)
                        if  tax_key in detalle_impuestos.keys():
                            detalle_impuestos[tax_key] += line.tax_ids_after_fiscal_position and line.tax_ids_after_fiscal_position[0].price_include and line.price_subtotal_incl or line.price_subtotal
                        else:
                            detalle_impuestos[tax_key]  = line.tax_ids_after_fiscal_position and line.tax_ids_after_fiscal_position[0].price_include and line.price_subtotal_incl or line.price_subtotal
            for key in detalle_impuestos.keys():
                tax_ids=key.split(",")
                tax_ids=[int(tax) for tax in tax_ids]
                tax=self.env['account.tax'].browse(tax_ids)[0]
                if not tax or tax.amount==0.0:
                    account_id=self.invoice_product.cuenta_tasa_0.id
                else:
                    
                    account_id=self.invoice_product.cuenta_tasa_16.id
                tax_ids =[key for key in tax_ids if key] 
                inv["invoice_line_ids"].append((0,0,
                                       {
                                       'quantity': 1,
                                       'product_id':self.invoice_product.id,
                                       'product_uom_id':self.invoice_product.uom_id.id,
                                       'account_id':account_id,
                                       'name': 'Orden No.: %s' % (pedido.name),
                                       'discount': 0.0,
                                       'price_unit': detalle_impuestos[key],
                                       'tax_ids': [(6,0,tax_ids)],
                                       'analytic_account_id': self.analytic_account_id.id,
                                      })) 
        inv_id = invoice_obj.create(inv)
        if not inv_id: 
            raise except_orm('Error',' No se generó la factura')

        for pedido in self.pedidos_pos: 
            pedido.write({'account_move': inv_id.id,'state': 'invoiced'})
            '''
            Check if pedido has devoluciones
            '''
            devoluciones=self.devoluciones_pos.filtered(lambda order: order.pos_reference == pedido.pos_reference)
            if devoluciones:
                '''
                Actualizar 
                '''
                for devolucion in devoluciones: 
                    devolucion.write({'account_move': inv_id.id,'state': 'invoiced'})
         
        inv_id._onchange_partner_id()
        inv_id._compute_amount() # Esto calcula las lineas de impuesto correctamente

        mod_obj = self.env['ir.model.data']
        res = mod_obj.get_object_reference('account', 'view_move_form')
        res_id = res and res[1] or False
        return {
            'name': _('Customer Invoice'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [res_id],
            'res_model': 'account.move',
            'context': "{'type':'out_invoice'}",
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': inv_id.id,
        }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
