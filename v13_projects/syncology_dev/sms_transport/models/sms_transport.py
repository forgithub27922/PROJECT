# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
import requests, json
from datetime import datetime, timedelta
from datetime import datetime
from datetime import date
from _ast import Try
from email.policy import default
from odoo.addons.test_convert.tests.test_env import field
import string


class RegisterStudentTransport(models.Model):
    _name = 'register.student.transport'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'register.student.transport'

    def set_regno(self):
        id = self.student_id.student_id
        self.name = "TR"+str(id)
        return

    def confirm_registration(self):
        self.state = 'registered'
        self.date_registered = fields.Date.today()
        self.registered_by = self._uid
        self.set_regno()
        return

    def withdraw_from_transport(self):
        self.state = 'withdrawal'
        self.date_registered = fields.Date.today()
        self.withdrawn_by = self._uid
        transport_sch = self.env['transport.scheduling'].search([])
        for schedule in transport_sch:
            schedule.write({'students_ids': [(3, self.id)]})

        return

    @api.onchange('student_id')
    def onchange_transport_student_address_contact_information(self):
        self.main_street = self.student_id.address
        self.city = self.student_id.city
        self.father_mobile = self.student_id.father_landline_number
        self.mother_mobile = self.student_id.mother_landline_number
        self.guardian_mobile = self.student_id.guardian_landline_number

    @api.onchange('student_id')
    def onchange_student_domain(self):
        std_list = []
        std_ids = self.search([('state', '=', ['draft', 'registered'])])
        for s in std_ids:
            std_list.append(s.student_id.id)
        return {'domain': {'student_id': [('id', 'not in', std_list), ('state', '=', 'admitted')]}}

    def unlink(self):
        for student in self:
            if student.state != 'draft':
                raise UserError(('Record can only be deleted in Draft State. Use the option of withdraw instead.'))
            else:
                return super(RegisterStudentTransport, self).unlink()

    def set_to_draft(self):
        """
        This method will be used to set the state as draft
        --------------------------------------------------
        @param self: object pointer
        """
        for stud_tran in self:
            stud_tran.state = 'draft'

    @api.depends('student_id.first_name_arabic', 'student_id.middle_name_arabic', 'student_id.second_middle_name_arabic', 'student_id.last_name_arabic')
    def _compute_student_name_arabic(self):
        for rec in self:
            rec.student_name_arabic = rec.student_id.full_name_arabic

    name = fields.Char(string='Reg No')
    student_id = fields.Many2one('academic.student', domain="[('state','=','admitted')]", string="Student",
                                 tracking=True)
    student_name_arabic = fields.Char(compute='_compute_student_name_arabic', string='Student Name Arabic', tracking=True, store=True)
    class_grade = fields.Many2one('school.class', string='Grade', related='student_id.class_id')
    bus_id = fields.Many2one('fleet.vehicle', string='Bus', tracking=True)
    count_in = fields.Integer(string='Count')
    count_out = fields.Integer(string='Count out')
    primary_handover = fields.Char('Primary Handover', related='student_id.family_id.name', store=True)
    secondary_handover = fields.Char('Secondary Handover')
    family_condition = fields.Selection(
        [('stable', 'Stable'), ('seperated', 'Seperated'), ('sensitively', 'Sensitively')], default='stable',
        string='Family Condition')
    city = fields.Many2one('res.city', tracking=True)
    father_mobile = fields.Char(string = 'Father Phone')
    mother_mobile = fields.Char(string = 'Mother Phone')
    guardian_mobile = fields.Char(string = 'Guardian Phone')
    main_street = fields.Char('Main Street', tracking=True)
    bystreet = fields.Char('By Street', tracking=True)
    more_details = fields.Text('More Details')
    registered_by = fields.Many2one('res.users', string="Registered By")
    date_registered = fields.Date('Date Registered')
    withdrawn_by = fields.Many2one('res.users', string="Withdrawn By")
    date_withdrawn = fields.Date('Date Withdrawn')
    state = fields.Selection([('draft', 'Draft'), ('registered', 'Registered'), ('withdrawal', 'Withdrawal')],
                             default='draft', string='State', tracking=True)
    email = fields.Char(related='student_id.guardian_email', string='Email')
    active = fields.Boolean('Active', default=True)
    installment_id = fields.Many2one('fee.policy.line', string='Installment ID')


class TransportRouteStop(models.Model):
    _name = 'transport.route.stop'
    _description = 'transport.route.stop'

    def unlink(self):
        raise UserError(('Deletion not allowed'))

    name = fields.Char('Route Stop')
    active = fields.Boolean('Active', default=True)
    rout_ids = fields.Many2many('transport.route', ondelete='restrict')
    buses_ids = fields.Many2many('fleet.vehicle', ondelete='restrict')


class TransportRoute(models.Model):
    _name = 'transport.route'
    _description = 'transport.route'

    def unlink(self):
        raise UserError(('Deletion not allowed'))

    name = fields.Char('Route')
    start_point = fields.Char('Start Point', tracking=True)
    end_point = fields.Char('End Point', tracking=True)
    stops_ids = fields.Many2many('transport.route.stop', string='Stop')
    busses_ids = fields.Many2many('fleet.vehicle')
    active = fields.Boolean('Active', default=True)


class VehicleModel(models.Model):
    _name = 'fleet.vehicle.model'
    _inherit = 'fleet.vehicle.model'
    _order = 'name asc'

    @api.depends('name', 'brand_id')
    def name_get(self):
        """Acutal name of the model is changed to make it simple, name_get() is overriden from orignal method """
        res = []
        for record in self:
            name = record.name
            res.append((record.id, name))
        return res


class TransportBus(models.Model):
    _name = 'fleet.vehicle'
    _inherit = 'fleet.vehicle'

    @api.depends('model_id.name', 'license_plate')
    def _compute_vehicle_name(self):
        for record in self:
            #             record.name = 'Not Set'
            record.name = str(record.model_id.name) or '--' + '/' + str(record.license_plate or ('--'))

    def get_bus_student_list(self, state, bus_id):
        lst = self.env['register.student.transport'].search([('state', '=', state), ('bus_id', '=', bus_id)])
        return lst

    def vehicle_stdent_con(self):
        #         self.ensure_one()
        # @sir shihid plz see this issue  i  have ensure one but still give multiple record
        for f in self:
            std_lst = self.get_bus_student_list('registered', f.id)
        self.veh_std_count = len(std_lst)
        return

    def return_action_to_open_student(self):
        return {
            'name': 'Student',
            'view_type': 'form',
            'view_mode': 'tree',
            'view_id': self.env.ref('sms_core.sms_core_academic_student_tree').id,
            'res_model': 'academic.student',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'domain': [('id', 'in', [x.student_id.id for x in self.get_bus_student_list('registered', self.id)])],
        }

    def unlink(self):
        raise UserError(('Deletion is not allowed'))

    bus_number = fields.Integer(string='Bus Number')
    vehical_driver_history_id = fields.Char('vehical.driver.history')
    state = fields.Selection(
        [('in_operation', 'Operational'), ('maintenance', 'Down For Maintenance'), ('permanently_down', 'Removed')],
        default='in_operation', string='State')
    veh_std_count = fields.Char(compute='vehicle_stdent_con', string='Strength')
    period = fields.Selection([('first', 'First'), ('second', 'Second')], default="first", string='Period')
    routes_ids = fields.Many2many('transport.route', 'vehicle_route_rel', 'vehicle_id', 'route_id', string='Routes')
    vehicle_driver_id = fields.Many2one('hr.employee', string='Driver', domain="[('job_id.name', 'in', ['Driver', 'سائق'])]")
    driver_contact_no = fields.Char('Contact No', related='vehicle_driver_id.mobile_phone')
    supervisor_id = fields.Many2one('hr.employee', string='Supervisor', domain="[('extra_activity_id.name', 'in', ['Supervisor', 'Bus Supervisor', 'مشرفة باص', 'مشرفة'])]")
    supervisor_contact_no = fields.Char('Contact No', related='supervisor_id.mobile_phone')
    route = fields.Many2one('transport.route', string='Route', domain="[('active','=',True)]")
    bus_description = fields.Char('Description')
    name = fields.Char(string='Vehicle', compute='_compute_vehicle_name')


class TransportComplaintManagement(models.Model):
    _name = 'transport.complaint.management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'transport.complaint.management'

    def set_copno(self):
        #         print("set complaint management system")
        #         sql = """select COALESCE(max(id),'0') from transport_complaint_management where state = 'resolved_by'"""
        #         self.env.cr.execute(sql)
        #         idd = self.env.cr.fetchone()[0]
        #         idd = int(idd)+1
        #         print("this is complaint no",idd)
        for record in self:
            record.complaint_no = "CMP" + str(record.id).zfill(4)
        return

    def resolved_complaint(self):
        self.resolved_by = self._uid
        self.date_resolved = datetime.now()
        self.set_copno()
        return {
            'name': _('Resolve Complaint Wizard'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'res_model': 'transport.complaint.resolve.wizard',
            'target': 'new',
        }

    def cancel_complaint(self):
        cancel_date = datetime.now()
        cancel_by = self._uid
        self.state = 'closed'

    def _compute_complaint_name(self):
        for record in self:
            record.name = 'CMP' + str(record.id).zfill(4)
        return
    
    @api.depends('student_name.first_name_arabic', 'student_name.middle_name_arabic', 'student_name.second_middle_name_arabic', 'student_name.last_name_arabic')
    def _compute_student_name_arabic(self):
        for rec in self:
            rec.student_name_arabic = rec.student_name.full_name_arabic

    name = fields.Char(string = 'No',compute='_compute_complaint_name')
    complaint_no =fields.Char(string = 'Complaint No',compute='set_copno')
    escalated = fields.Boolean('Escalated',default = True)
    bus_number = fields.Many2one('fleet.vehicle', string='Bus',domain=[('active', '=',True)],tracking=True)
    period =  fields.Selection([('first','First'),('second', 'Second')], default='first',string='Period')
    driver_name = fields.Many2one('hr.employee', string='Driver', related='bus_number.vehicle_driver_id')

    driver_phone = fields.Char(related='driver_name.mobile_phone',string ='Mobile Number ')
    supervisor_name = fields.Many2one('hr.employee', string='Supervisor', related='bus_number.supervisor_id')

    supervisor_phone = fields.Char(related='supervisor_name.mobile_phone',string ='Mobile Number ')
    complain_from =  fields.Selection([('student','Student'),('driver', 'Driver'),('supervisor', 'Supervisor')], default='student',string='Complain From',tracking=True)
    complain_against =  fields.Selection([('student','Student'),('driver', 'Driver'),('supervisor', 'Supervisor')],default='driver', string='Complain Against',tracking=True)
    student_name = fields.Many2one('academic.student', string='Student',tracking=True)
    student_name_arabic = fields.Char(compute='_compute_student_name_arabic', string='Student Name Arabic', tracking=True, store=True)
    date = fields.Date(string ='Date of Incident')
    severity =  fields.Selection([('low','Low'),('medium', 'Medium'),('high', 'High'),('major', 'Major')],default='low', string = 'Severity',tracking=True)
    complain=fields.Text(string = 'Complain')
    state = fields.Selection([('received', 'Reported'),('resolved', 'Resolved'),('closed', 'Closed')],default = 'received',string = 'State',tracking=True)
    resolve_type = fields.Selection([('check', 'Check'),('uncheck', 'Uncheck')], store=False)
    resolved_by = fields.Many2one('hr.employee', string='Resolved by')
    date_resolved = fields.Date(string='Resolved Date')
    cancel_by = fields.Many2one('hr.employee', string='Cancel by')
    cancel_date = fields.Date(string ='Cancel Date')
    complaint_reporter_id = fields.Many2one('complaint.reporter', 'Complaint Reporter', default=lambda self:self.get_default())
    resolve = fields.Text(string = 'Resolve')

    def get_default(self):
        complain = self.env['complaint.reporter'].search([], limit=1)
        return complain

    def unlink(self):
        raise UserError(('Deletion not allowed'))


class TransportScheduling(models.Model):
    _name = 'transport.scheduling'
    _description = 'transport.scheduling'

    _sql_constraints = [
        ('unique_schedule_days_bus', 'unique (schedule_days,bus_id)', 'The scheduling for this day is already existing!')
    ]

    def _compute_schedule_name(self):
        for record in self:
            record.name = 'SCH' + str(record.id).zfill(4) + "-" + str(record.bus_id.license_plate)
        return

    name = fields.Char(string = 'No',compute='_compute_schedule_name')
    schedule_days = fields.Many2one('sms.scheduling.days', 'Scheduling Days')
    bus_id = fields.Many2one('fleet.vehicle', string='Bus',domain=[('active', '=',True)])
    driver_id = fields.Many2one('hr.employee', string='Driver', domain="[('job_id.name', 'in', ['Driver', 'سائق'])]")
    supervisor_id = fields.Many2one('hr.employee', string='Supervisor', domain="[('extra_activity_id.name', 'in', ['Supervisor', 'Bus Supervisor', 'مشرفة باص', 'مشرفة'])]")
    routes_ids = fields.Many2many('transport.route','schedul_route_rel','schedul_id','route_id', string='Routes', related='bus_id.routes_ids')
    students_ids = fields.Many2many('register.student.transport')
    state = fields.Selection([('draft', 'Draft'), ('active', 'Active'), ('closed', 'Closed'), ('cancel', 'Cancel')],
                             string='State', default='draft')
    supervisor_phone_no = fields.Char('Supervisor Phone Number')
    driver_phone_no = fields.Char('Driver Phone Number')

    
    @api.onchange('bus_id')
    def onchange_fill_student(self):
        if self.bus_id:
            std_ids = self.env['register.student.transport'].search([('bus_id', '=', self.bus_id.id)])
            self.students_ids = std_ids.ids
            self.driver_id = self.bus_id.vehicle_driver_id
            self.supervisor_id = self.bus_id.supervisor_id
            self.driver_phone_no = self.bus_id.vehicle_driver_id.mobile_phone
            self.supervisor_phone_no = self.bus_id.supervisor_id.mobile_phone
        

    def unlink(self):
        if self.state != 'draft':
            raise UserError(('Record can only be deleted in Draft State.'))

        return super(TransportScheduling, self).unlink()


class HrEmployee(models.Model):
    _name = 'hr.employee'
    _inherit = 'hr.employee'

    def unlink(self):
        if self.env.user.has_group('sms_transport.group_manager_sms_transport') \
                or self.env.user.has_group('sms_transport.group_officer_sms_transport'):
            if not self.env.user.has_group('hr.group_hr_manager') \
                    and not self.env.user.has_group('hr.group_hr_user'):
                raise UserError(_('You Cannot Delete Record'))

        return super(HrEmployee, self).unlink()

    buses_ids = fields.One2many('fleet.vehicle','vehicle_driver_id', string='Vehicles')
    extra_activity_id = fields.Many2one('extra.activity', string='Extra Activity')

    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        args = args or []
        if self._context.get('employee_driver', False):
            if self.env.company.job_position_id:
                args += [('job_id', '=', self.env.company.job_position_id.id)]

        if self._context.get('employee_supervisor', False):
            if self.env.company.extra_activity_id:
                args += [('extra_activity_id', '=', self.env.company.extra_activity_id.id)]

        return super(HrEmployee, self)._search(args, offset=offset, limit=limit, order=order, count=count,
                                               access_rights_uid=access_rights_uid)

    def write(self, vals):
        """
        Overridden write() method to archived/unarchived driver and supervisor
        ----------------------------------------------------------------------
        :param self: object pointer
        :param vals: a dictionary containing fields and values
        :return: True
        """
        if self.env.user.has_group('sms_transport.group_manager_sms_transport') \
                or self.env.user.has_group('sms_transport.group_officer_sms_transport'):
            if not self.env.user.has_group('hr.group_hr_manager') \
                    and not self.env.user.has_group('hr.group_hr_user'):
                if vals.get('active'):
                    raise UserError(_('You cannot archive driver/supervisor'))

        return super().write(vals)

    @api.model
    def name_search(self, name='', args=None, operator='ilike',limit=100):
        """
        Overridden name_search method to search based on name and code
        --------------------------------------------------------------
        :param self: object pointer
        :param name: the string typed in for searching the name
        :param args: the domain passed on the field
        :param operator: default is ilike so can search the matching string
        :param limit: max no of records
        """
        dom = ['|', '|', '|', '|', '|', '|', '|', '|', '|',
               ('name', operator, name),
               ('full_name_arabic', operator, name),
               ('middle_name', operator, name),
               ('last_name', operator, name),
               ('fourth_name', operator, name),
               ('first_name_arabic', operator, name),
               ('middle_name_arabic', operator, name),
               ('last_name_arabic', operator, name),
               ('fourth_name_arabic', operator, name),
               ('display_name', operator, name)]
        if args:
            dom += args
        employee_name = self.search(dom)
        return employee_name.name_get()

class ExtraActivity(models.Model):
    _name = 'extra.activity'
    _description = 'extra.activity'

    name = fields.Char('Name')
    code = fields.Char('Code')


class ComplaintReporter(models.Model):
    _name = 'complaint.reporter'
    _description = 'complaint.reporter'

    name = fields.Char('Name', required=True)
    code = fields.Char('Code')


class SmsSchedulingDays(models.Model):
    _name = 'sms.scheduling.days'
    _description = 'sms.scheduling.days'

    _sql_constraints = [('unique_name', 'unique(name)', 'Scheduling Days must be unique')]

    name = fields.Char('Name')
    code = fields.Char('Code')

