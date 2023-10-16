from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, Warning
from datetime import datetime, timedelta


class HRlifecycleWizard(models.TransientModel):
    _name = 'hr.lifecycle.wizard'

    status = fields.Selection([('joined', 'Joined'), ('training', 'Training'),
                               ('ex-training', 'Extended Training'),
                               ('probation', 'Probation'),
                               ('ex-probation', 'Extended Probation'),
                               ('employment', 'Employment'),
                               ('pip', 'PIP'),
                               ('notice_period', 'Notice Period'),
                               ('relieved', 'Relieved'),
                               ('terminated', 'Terminated'),
                               ('rejoined', 'Rejoined')],
                              string='Status', readonly=True)
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    terminate_note = fields.Text("Terminate Reason")
    company_id = fields.Many2one('res.company', 'Company',
                                 default=lambda self: self.env.user.company_id)

    @api.constrains('start_date', 'end_date')
    def check_date(self):
        employee_obj = self.env['hr.employee']
        res_emp = employee_obj.browse(self._context.get('active_id'))
        emp_history = res_emp.status_history
        if not emp_history:
            raise Warning(_("This employee has not joined yet...!!"))
        last_rec_id = max(emp_history)
        last_id_end_date = last_rec_id.end_date
        chk_lst = ["pip", "notice_period", "relieved", "terminated"]
        for rec in self:
            start_date = rec.start_date
            end_date = rec.end_date
            status = rec.status
            if last_id_end_date and status not in chk_lst \
                and not start_date >= last_id_end_date:
                raise Warning(_("Please Enter Valid Date..!"))
            if status in chk_lst and not start_date >= last_rec_id.start_date:
                raise Warning(_("Please Enter Valid Date..!"))
            if end_date and not end_date > start_date:
                raise Warning(_("End Date should be greater than start "
                                "date..!"))
            if rec.start_date:
                if rec.start_date < res_emp.date_joining:
                    raise ValidationError(_('Start date should be less than Joining Date'))
            if rec.start_date and rec.end_date:
                if rec.start_date < res_emp.date_joining and rec.end_date < res_emp.date_joining:
                    raise ValidationError(_('Start date and end date should be less than Joining Date'))

    @api.multi
    def change_status(self):
        employee_obj = self.env['hr.employee']
        res_emp = employee_obj.browse(self._context.get('active_id'))
        end_state_list = ["employment", "relieved", "rejoined", "terminated",
                          "notice_period"]
        for rec in self:
            status = rec.status
            start_date = rec.start_date
            end_date = rec.end_date
            emp_history = res_emp.status_history
            emp_filter = emp_history.filtered(lambda m: m.is_emp is False and
                                              m.state == 'employment')
            last_rec_id = max(emp_history)
            last_rec_status = last_rec_id.state
            end_date_dict = start_date
            if not end_date_dict == last_rec_id.start_date:
                end_date_dict = datetime.strptime(start_date, '%Y-%m-%d')\
                    - timedelta(days=1)
            status_dict = {'state': status, 'start_date': start_date}
            if status not in end_state_list:
                status_dict.update({'end_date': end_date})
            create_rec_st_ed = (0, 0, status_dict)
            create_rec_st_st = (0, 0, {'state': status,
                                       'start_date': start_date,
                                       'end_date': start_date})
            write_end_date = (1, last_rec_id.id, {'end_date': end_date_dict})
            emp_st_dict = {'status': status, 'emp_id':res_emp.id}
            status_list = ['training', 'ex-training', 'probation',
                           'ex-probation',"joined"]
            if status == 'training':
                emp_st_dict.update({'status_history': [create_rec_st_ed],
                                    'is_training': True})
                if last_rec_status == 'rejoined':
                    emp_st_dict.update({'is_ex_training': False,
                                        'is_probation': False,
                                        'is_notice_period': False})

            elif status == 'ex-training':
                emp_st_dict.update({'status_history': [create_rec_st_ed],
                                    'is_ex_training': True})

            elif status == 'probation':
                emp_st_dict.update({'status_history': [create_rec_st_ed],
                                    'is_probation': True,
                                    'date_employment': start_date})
                if last_rec_status == 'rejoined':
                    emp_st_dict.update({'is_ex_probation': False,
                                        'is_employment': False,
                                        'is_notice_period': False})

            elif status == 'ex-probation':
                emp_st_dict.update({'status_history': [create_rec_st_ed],
                                    'is_ex_probation': True,
                                    'is_employment': False})

            elif status == 'employment':
                if last_rec_status in status_list:
                    if res_emp.date_employment:
                        emp_st_dict.update({'status_history': [create_rec_st_ed],
                                            'is_employment': True,
                                            'is_pip': False,
                                            'is_notice_period': False,
                                            'date_confirmation': start_date})
                    else:
                        emp_st_dict.update({'status_history': [create_rec_st_ed],
                                            'is_employment': True,
                                            'is_pip': False,
                                            'is_notice_period': False,
                                            'date_employment': start_date,
                                            'date_confirmation': start_date})
                elif last_rec_status == 'pip':
                    for empl in emp_filter:
                        emp_st_dict.update({'is_pip': False,
                                            'status_history': [create_rec_st_ed]})
                        if last_rec_status == 'employment' and last_rec_id.end_date is False:
                            emp_histry_ed = (1, empl.id, {'end_date':
                                               start_date})
                            emp_st_dict.update({'status_history': [emp_histry_ed,
                                                                   create_rec_st_ed],
                                                'is_pip': True, 'is_employment': False})
                if last_rec_status == 'notice_period':
                    emp_st_dict.update({'status_history': [create_rec_st_ed],
                                        'is_employment': False})
            elif status == 'pip':
                emp_st_dict.update({'status_history': [create_rec_st_ed],
                                    'is_pip': True, 'is_employment': False})
                if last_rec_status == 'employment' and last_rec_id.end_date is False:
                    emp_filter1 = emp_history.filtered(lambda m: m.is_emp is False and
                                              m.state == 'employment' and m.end_date is False)
                    for emp_histry in emp_filter1:
                        if emp_histry.end_date is False:
                            emp_histry_ed = (1, emp_histry.id, {'end_date':
                                               start_date})
                            emp_st_dict.update({'status_history': [emp_histry_ed,
                                                               create_rec_st_ed],
                                            'is_pip': True, 'is_employment': False})
            elif status == 'notice_period':
                emp_st_dict.update({'status_history': [create_rec_st_ed],
                                    'is_notice_period': True,
                                    'is_relieved': False})
            elif status == 'relieved' and last_rec_id.is_np is False:
                emp_st_dict.update({'status_history':
                                    [(1, last_rec_id.id, {'end_date':
                                                          start_date,
                                                          'is_np': True}),
                                     create_rec_st_st], 'is_relieved': True,
                                    'is_rejoined': False})

            elif status == 'rejoined':
                emp_st_dict.update({'status_history': [create_rec_st_st],
                                    'is_rejoined': True, 'is_training': False,
                                    'is_probation': False})

            elif status == 'terminated':
                emp_st_dict.update({'is_terminated': True,
                                    'notes': rec.terminate_note})
                for empl in emp_filter:
                    stat_tup = (1, empl.id, {'is_emp': True, 'end_date':
                                             end_date_dict})
                    if last_rec_status == 'employment':
                        emp_st_dict.update({'status_history': [write_end_date,
                                                               create_rec_st_st]})
                    elif last_rec_status in status_list:
                        emp_st_dict.update({'status_history': [create_rec_st_st]})
                    elif last_rec_status == 'pip':
                        if emp_filter:
                            emp_st_dict.update({'status_history':
                                                [stat_tup, create_rec_st_st]})

            res_emp.write(emp_st_dict)
        return True
