# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2012 (http://www.bistasolutions.com)
#
##############################################################################

from odoo import api, fields, models, _ , exceptions
from datetime import datetime,timedelta
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval
from dateutil.relativedelta import relativedelta
from dateutil import parser


class DynamicMail(models.Model):
    _name = "dynamic.mail"
    _description ='Dynamic Mail'

    @api.multi
    def is_mail_sent(self):
        for res in self:
            if not res.mail_ids:
                res.all_mail_sent = False
                continue

            if any(x!='sent' for x in res.mail_ids.mapped('state')):
                res.all_mail_sent = False
            else:
                res.all_mail_sent = True
    
    @api.constrains('select_time')
    def check_select_time_greater_than_zero(self):
        if not self.select_time >0 :
            raise exceptions.Warning('Please Enter Greater than zero value in Trigger before')

    name = fields.Char(string='Name', default='New', copy = False)
    send_mail_to = fields.Selection([('group','Groups'),('user','Users')],string='Send Mail To?',default='user')
    groups_ids = fields.Many2many('res.groups',string='Groups')
    user_ids = fields.Many2many('res.users',string='Users')
    field_id = fields.Many2one('ir.model.fields')
    model_id = fields.Many2one('ir.model')
    model_name = fields.Char(string='Model Name', related='model_id.model', readonly=True, store=True)
    before_or_after = fields.Selection([('before','Before'),('after','After'),('same_day','Same Day')],default='before')
    select_time = fields.Integer(string='before x time')
    select_month_days = fields.Selection([('days','Days'),('months','Months')],string='set Months or Days',default='months')
    template_id = fields.Many2one('mail.template',string='Template')
    active = fields.Boolean(string='Active',default=True)  
    cron_id = fields.Many2one('ir.cron',string='Cron',copied=False)
    domain_filter = fields.Char(string='Filter', default='[]')
    mail_ids = fields.One2many('mail.mail','dynamic_config_id',string='Mails')
    all_mail_sent = fields.Boolean(compute="is_mail_sent",string="Is All Mail Sent?",default=False)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env['res.company']._company_default_get('property.erec'))


    @api.multi
    @api.onchange('groups_ids')
    def onchange_groups_ids(self):
        if self.user_ids:
            self.user_ids = False
        if self.groups_ids:
            return {'domain':{'user_ids':[('id','in',self.groups_ids.mapped('users.id'))]}}
    
    @api.multi
    @api.onchange('model_id')
    def onchange_model_id(self):
        # if self.model_id:
            self.write({'field_id':False,'template_id':False})

    @api.model
    def create(self,vals):
        if vals.get('name', 'New') == 'New':
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('dynamic.mail') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('dynamic.mail') or 'New'
        if self.send_mail_to=='group' and vals and not vals.get('user_ids')[0][2] :
            users = self.env['res.groups'].browse(vals.get('groups_ids')[0][2]).mapped('users.id')
            vals.update({'user_ids':[(6,0,users)]})
        res = super(DynamicMail, self).create(vals)

        cron = self.env['ir.cron'].create({'model_id':vals.get('model_id'),'state':'code',
                                'name':vals.get('name'),'nextcall':datetime.now(),'numbercall':-1,
                                'template_id':vals.get('template_id'),'interval_number':8,
                                'code':'env["dynamic.mail"].send_mail('+str(res.id)+')','interval_type':'hours'})

        res.update({'cron_id':cron.id})
        return res

    # @api.onchange('active')
    # @api.depends('active')
    # def onchange_active_dynamic_mail(self):
    #     if self.cron_id:
    #         self.cron_id.write({'active':self.active})

    @api.multi
    def send_mail(self,id):
        mail_ids=[]
        domain_expr = []
        res = self.env['dynamic.mail'].browse(id)
        model_name= res.cron_id.model_id.model
        if res.domain_filter:
            domain_expr =safe_eval(res.domain_filter)
        recs = self.env[model_name].search(domain_expr)
        time = res.select_time
        m_or_d = res.select_month_days
        mail_obj = self.env['mail.mail']
        for rec in recs:
            date = rec.mapped(res.field_id.name) and rec.mapped(res.field_id.name)[0]
            if date:
                date = parser.parse(date)
                if res.before_or_after =='same_day':
                    if date.today().date() == date.date():
                        Flag = True
                    else:
                        Flag  = False
                elif res.before_or_after =='before':
                    if m_or_d == 'days':
                        date = date - timedelta(days=time)
                    else:
                        date = date - relativedelta(months=time)
                    
                    if date <= date.today():
                        Flag = True
                    else:
                        Flag = False
                elif res.before_or_after =='after':
                    if m_or_d == 'days':
                        date = date + timedelta(days=time)
                    else:
                        date = date + relativedelta(months=time)
                    if date >= date.today():
                        Flag = True
                    else:
                        Flag = False
                    
                if Flag and not mail_obj.search([('res_id','=',rec.id),('model','=',model_name)]):
                    try:
                        mail_id = res.template_id.send_mail(rec.id)
                        mail_ids.append(mail_id)
                    except:
                        pass
        emails = []
        for email in res.user_ids.mapped('email'):
            if email:
                emails.append(email)

        mails =  ','.join(list(set(tuple(emails))))
        for mail in self.env['mail.mail'].browse(mail_ids):
            mail.email_to += mails
            mail.dynamic_config_id = id 
            mail.write({'auto_delete':False})
           
        
    def write(self,vals):
        if vals.get('send_mail_to')=='group' or self.send_mail_to=='group' and not (vals.get('user_ids')and vals.get('user_ids')[0][2]):
            vals.update({'user_ids': [(6,0,self.groups_ids.mapped('users.id'))]})
        if 'active' in vals:
            self.cron_id.active = vals.get('active')
        return super(DynamicMail,self).write(vals)

