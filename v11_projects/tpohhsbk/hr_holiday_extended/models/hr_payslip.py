from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'


    
    
    @api.multi
    def action_payslip_done(self):
        """Calculate payroll based on leave encashment
                leave encash in current month. For e.g.
                 Payslip date: 5/1/2018-5/31/2018
                and have leave encash date
                 Payslip date: 5/1/2018-5/31/2018 ."""
        for rec in self:
            if not rec.contract_id:
                raise ValidationError(_('Please define contract for employee %s '
                                        % (rec.employee_id.name)))
            encashment_obj = self.env['leave.encashment']
            encashment_ids = encashment_obj.search([
                ('employee_id', '=', rec.employee_id.id),('encash_date','>=',rec.date_from),('encash_date','<=',rec.date_to),
                ('state', '=', 'approved'),('leave_encashment_payment_mode','=','salary')])
            
            rec.encash_amount = sum(encashment.encash_amount for encashment in
                                 encashment_ids)
            
            for encashment in encashment_ids:
                for leave in encashment.allocation_ids:
                    leave.state = 'encashed'
                encashment.state = 'paid'
                encashment.payslip_id = rec.id
                
                lapse_leave = self.env['hr.holidays'].search([('encashment_id','=',encashment.id)])
                if lapse_leave:
                    lapse_leave.write({'encash_amount': encashment.encash_amount * -1})
                    
                    
        return super(HrPayslip, self).action_payslip_done()


    """ Removed encashment from payslip"""
    @api.depends('date_from', 'date_to', 'employee_id')
    def _calculate_encashment_amount(self):
        for rec in self:
            leave_encash_rec = self.env['leave.encashment']
            encashment_ids = leave_encash_rec.search([
                ('employee_id', '=', rec.employee_id.id),('encash_date','>=',rec.date_from),('encash_date','<=',rec.date_to),
                ('state', '=', 'approved'),('leave_encashment_payment_mode','=','salary')])
            rec.encash_amount = sum(encashment.encash_amount for encashment in
                                 encashment_ids)
            

    encash_amount = fields.Float(string='Encashment Amount',
                                 compute='_calculate_encashment_amount',
                                 store=True)
    encashment_ids = fields.One2many('leave.encashment','payslip_id',string='Encashments')
    
    @api.multi
    def action_set_to_draft(self):
        res = super(HrPayslip,self).action_set_to_draft()
        for rec in self:
            rec.encashment_ids.write({'state':'approved'})
        return res
        
        
