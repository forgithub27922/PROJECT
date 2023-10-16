# -*- encoding: utf-8 -*-
##############################################################################
#
#    Bista Solutions Pvt. Ltd
#    Copyright (C) 2016 (http://www.bistasolutions.com)
#
##############################################################################


from odoo import fields, models, api, _
from odoo.exceptions import Warning
from datetime import datetime,date
import base64
import xlrd


class wizard_import_trial_balance(models.TransientModel):
    _name ='wizard.import.trial.balance'


    date = fields.Date(string="Date",default=date.today())
    company_id = fields.Many2one('res.company',string="Company",default=lambda self: self.env.user.company_id)
    state = fields.Selection([('init', 'init'), ('done', 'done')],
                             string='Status', readonly=True, default='init')
    name = fields.Char('File Name')
    file_upload = fields.Binary('File to Upload',filetype='PNG')
    journal_id = fields.Many2one('account.journal',string="Journal")
    trial_balance_line_ids = fields.One2many('wizard.import.trial.balance.line','import_trial_balance_id',string="Trial balance")
    ref = fields.Char('Reference') 

    @api.onchange('company_id')
    def onchange_comany_id(self):
        self.journal_id  = False
        return {'domain':{'company_id':[('id','=',self.env.user.company_id.id)]}}
    
    @api.multi
    def do_import_trial_balance(self):
        account_account_obj = self.env['account.account'].sudo()
        account_move_line_obj = self.env['account.move.line'].sudo()
        if not self.file_upload:
            raise Warning(_('Please Upload XLS file.'))
        
        try:
            missing_account_lst = []
            move_line_lst = []
            read_file = base64.decodestring(self.file_upload)
            book = xlrd.open_workbook(file_contents=read_file)
            sheet = book.sheet_by_index(0)

            for row_line in range(1,sheet.nrows):
                row_values = sheet.row_values(row_line)
                if len(row_values) != 4:
                    raise Warning(_('Please Enter Proper Data format. Format Shoud be like [Account Code, Account Name,Debit,Credit]'))

                if not row_values[0]:
                    raise Warning(('Account Code Missing.'))
                if not row_values[1]:
                    raise Warning(('Account Name Missing.'))

                debit = row_values[2] or 0.00
                credit = row_values[3] or 0.00
                if isinstance(row_values[0],float):
                    account_code = int(row_values[0])
                else:
                    account_code = str(row_values[0]).strip()
                account_name = row_values[1].strip()
                account_account_obj = account_account_obj.search([('code','=',account_code),
                                      ('company_id','=',self.company_id.id)],limit=1)

                line_amount = debit if debit else credit
                if not account_account_obj:
                    missing_account_lst.append((0,0,{'code':account_code,'name':account_name,
                                                    'company_id':self.company_id.id}))
                else:
                    move_line_ids = account_move_line_obj.search([('company_id','=',self.company_id.id),
                    ('account_id','=',account_account_obj.id),('date','<=',self.date),('move_id.state','=','posted')])
                    move_line_balance = abs(sum(move_line_ids.mapped('credit')) - sum(move_line_ids.mapped('debit')))

                    if not line_amount:
                        continue
                    if credit and debit:
                        raise Warning(_('Please Enter Proper Data.'))

                    line_amount = float("{:.2f}".format(line_amount))
                    final_amount = abs(move_line_balance - line_amount)
                    if not final_amount:
                        continue

                    move_lines = {
                            'name': self.ref,
                            'account_id': account_account_obj.id,
                            'journal_id': self.journal_id.id,
                            'date': self.date,
                            'debit': final_amount if debit else 0.00,
                            'credit': final_amount if credit else 0.00
                    }
                    move_line_lst.append((0,0,move_lines))

            if missing_account_lst:
                self.trial_balance_line_ids = False
                self.trial_balance_line_ids = missing_account_lst
                return self.do_go_back('done')
            else:
                self.create_trial_balance_move(move_line_lst)

        except Exception as e:
            raise Warning(_(e))

    @api.multi
    def do_create_account(self):
        account_account_obj = self.env['account.account'].sudo()
        for line in self.trial_balance_line_ids:
            if not line.user_type_id:
                raise Warning(_('Please Set Account Type.'))
            account_account_obj.create({'code':line.code,
                                        'name':line.name,
                                        'user_type_id':line.user_type_id.id,
                                        'group_id':line.group_id.id,
                                        'company_id':line.company_id.id or self.company_id.id,
                                        'reconcile':line.reconcile

            })
        self.do_import_trial_balance()
        # return self.do_go_back('init')

    @api.multi
    def do_go_back(self,state):
        self.state = state
        return {
            'name': 'Trial Balance',
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'target': 'new'
        }

    @api.multi
    def create_trial_balance_move(self,move_line_lst):
        # total_credit = total_debit = 0.00
        # for line in move_line_lst:
        #     total_credit += line[2]['credit']
        #     total_debit += line[2]['debit']

        if move_line_lst:
            vals = {
            'journal_id': self.journal_id.id,
            'date': self.date,
            'line_ids': move_line_lst,
            'ref': self.ref,
            'company_id':self.company_id.id,
            }
            self.env['account.move'].sudo().create(vals)


class wizard_import_trial_balance_line(models.TransientModel):
    _name ='wizard.import.trial.balance.line'

    import_trial_balance_id = fields.Many2one('wizard.import.trial.balance',string="Wizard")
    code = fields.Char(string="Code")
    name = fields.Char(string="Name")
    user_type_id = fields.Many2one('account.account.type',string="Type")
    group_id = fields.Many2one('account.group',string="Group")
    company_id = fields.Many2one('res.company',string="Company")
    reconcile = fields.Boolean(string="Allow Reconciliation")
