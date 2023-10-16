#########################################################################################
#
#    Copyright (C) 2019 Skyscend Business Solutions (http://www.skyscendbs.com)
#    Copyright (C) 2020 Skyscend Business Solutions Pvt. Ltd. (http://www.skyscendbs.com)
#
##########################################################################################
from datetime import date

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError,UserError
from odoo.tools import ustr


class Employee(models.Model):
    _inherit = 'hr.employee'
    _rec_name = 'display_name'

    salary = fields.Float('Salary')
    is_confidential = fields.Boolean('Is Confidential')
    hide_sal = fields.Boolean('Hide Salary', compute='_check_hide_sal')
    starting_date = fields.Date('Starting Date')
    annual_bonus = fields.Float('Annual Bonus')
    barcode = fields.Char(string="Badge ID", help="ID used for employee identification.", groups="base.group_user", copy=False)

    # Personal Data
    first_name_arabic = fields.Char('First Name (Arabic)')
    middle_name_arabic = fields.Char('Second Name (Arabic)')
    last_name_arabic = fields.Char('Third Name (Arabic)')
    fourth_name_arabic = fields.Char('Fourth Name (Arabic)')
    middle_name = fields.Char('Second Name')
    last_name = fields.Char('Third Name')
    fourth_name = fields.Char('Fourth Name')
    religion = fields.Char('Religion')
    birth_place = fields.Many2one('res.country.state', 'Place of Birth')
    gender_rec = fields.Selection([('male', 'Male'),
                               ('female', 'Female')], 'Gender')
    national_id = fields.Char('National ID', size=14)
    marital_status = fields.Selection([('unmarried', 'Unmarried'),
                                       ('married', 'Married'),
                                       ('divorced', 'Divorced'),
                                       ('widowed', 'Widowed')], 'Marital Status')
    address_rec = fields.Text('Address')
    phone_number = fields.Char('Phone Number', size=13)
    city_id = fields.Many2one('res.city', 'City')
    academic_qualification = fields.Char('Academic Qualification')
    military_status = fields.Selection([('done', 'Done'),
                                        ('relieved', 'Relieved'),
                                        ('uncharged', 'Uncharged')], 'Military Status')
    general_service_status = fields.Selection([('done', 'Done'),
                                               ('relieved', 'Relieved'),
                                               ('uncharged', 'Uncharged')], 'General Service Status')
    emp_email = fields.Char("Personal Email")

    # Family Information
    spouse_national_id = fields.Char('Partner National ID', size=14)
    spouse_academic_qualification = fields.Char('Partner Academic Qualification')
    spouse_place_of_birth = fields.Many2one('res.country.state', 'Partner Place of Birth')
    spouse_employment = fields.Char('Partner Employment')
    spouse_employment_location = fields.Char('Partner Employment Location')
    spouse_with_children = fields.Boolean('With Children?')

    # Training & Experience
    education_ids = fields.One2many('hr.education', 'employee_id', 'Education')
    training_ids = fields.One2many('hr.training', 'employee_id', 'Training')
    experience_ids = fields.One2many('hr.experience', 'employee_id', 'Experience')

    #Employee Status
    status_id = fields.Many2one('hr.employee.status', 'Status', check_company=True)

    #Insurance Information
    #Social Security
    contract_type_id = fields.Many2one('hr.employee.contract.type', 'Contract Type', check_company=True)
    social_security_number = fields.Char('Social Security Number')
    social_security_date = fields.Date('Date of Social Security')
    reason_no_insurance = fields.Char('Reason for No Insurance')
    #Health Insurance
    medical_check_done = fields.Boolean('Medical Check Done?')
    health_insurance_card_number = fields.Char('Health Insurance Card Number')
    release_date = fields.Date('Date of Release')
    #Labour Office
    contract_job_id = fields.Many2one('hr.job', 'Contracting Job', check_company=True)
    contract_date = fields.Date('Contract Date')
    date_work_certi = fields.Date('Date of Work Certificate')
    incoming_no = fields.Char('Incoming Number')

    display_name = fields.Char(compute="_compute_display_name", store=True)
    full_name_arabic = fields.Char(compute="_compute_employee_name_arabic", store=True)
    hourly_rate = fields.Float('Hourly Rate', compute='_calc_hourly_rate')

    job_history_ids = fields.One2many('job.history.line','history_id', string='job History')
    insurance = fields.Boolean('Insurance')
    ins_cut_value = fields.Float('Insurance cut value')
    fellowship_fund = fields.Boolean('Fellowship Fund')
    fellowship_cut_value = fields.Float('Fellowship Fund cut value')
    staff_children_cut = fields.Float('Staffs children cut')
    other_cut = fields.Float('Other cut')
    senior_allowance = fields.Float('Senior Allowance')
    transition_allowance = fields.Float('Transition Allowance')
    lms_allowance = fields.Float('LMS Allowance')
    travel_allowance_driver = fields.Float('Travel Allowance For Drivers')
    supervision_maintenance_allowance = fields.Float('Supervision and maintenance Allowance')
    other_allowance = fields.Float('Other Allowance')

    schedule_time_ids = fields.One2many('schedule.time', 'employee_id', 'Schedule')

    @api.onchange('schedule_time_ids', 'schedule_time_ids.from_date', 'schedule_time_ids.to_date')
    def onchange_schedule_time(self):
        number_lst = [num for num in range(0, 32)]
        line_number_lst = []
        for emp in self:
            blank_lines = emp.schedule_time_ids.filtered(lambda x: x.from_date == 0 and x.to_date == 0)
            for line in emp.schedule_time_ids:
                if line.from_date not in number_lst:
                    raise ValidationError("Start Date Must be between 1 to 31")
                elif line.to_date not in number_lst:
                    raise ValidationError("End Date Must be between 1 to 31")
                elif line.from_date and line.to_date and line.from_date >= line.to_date:
                    raise ValidationError("End Date Must be Greater Than Start Date")
                elif line.to_date and not line.from_date:
                    raise ValidationError("Start Date Must be required")
                elif line.from_date and not line.to_date:
                    raise ValidationError("End Date Must be required")
                elif len(blank_lines) > 1:
                    raise ValidationError("You should not keep more than one blank record")

                if line.from_date not in line_number_lst and line.to_date not in line_number_lst:
                    line_number_lst += [num for num in range(line.from_date, line.to_date+1)]
                else:
                    raise ValidationError("You can't Overlap Date")

    def update_emp_full_name_arabic(self):
        emps = self.search([])
        for emp in emps:
            emp.full_name_arabic = str(emp.first_name_arabic) + " " + str(emp.middle_name_arabic) + " " + str(emp.last_name_arabic) + " " + str(emp.fourth_name_arabic)

    @api.onchange('insurance', 'fellowship_fund')
    def onchange_insurance_fellowship_fund(self):
        """
        Onchange method to set Insurance cut value based on insurance and set Fellowship Fund cut value based
        on Fellowship Fund
        -----------------------------------------------------------------------------------------------------
        :param self: object pointer
        """
        if not self.insurance:
            self.ins_cut_value = 0.00
        if not self.fellowship_fund:
            self.fellowship_cut_value = 0.00

    @api.depends('salary', 'department_id')
    def _calc_hourly_rate(self):
        """
        compute method for the hourly rate based on the department.
        -----------------------------------------------------------
        :param self: object pointer
        """
        for emp in self:
            if emp.salary and emp.department_id.business_hours:
                emp.hourly_rate = emp.salary / 30 / emp.department_id.business_hours

            else:
                emp.hourly_rate = 0.0

    def _check_hide_sal(self):
        """
        Compute method for the hiding of field based on the confidential.
        -----------------------------------------------------------------
        @param self: object pointer
        """
        # Fetch User Groups
        user_groups = self.env.user.groups_id
        # fetch Employee manager groups
        manager_grp = self.env.ref('hr.group_hr_manager')
        flag = False
        if manager_grp in user_groups:
            flag = True
        # Calculate Hide Sal based on the Group Manager
        for emp in self:
            hide_sal = False
            if emp.is_confidential:
                hide_sal = not flag
            emp.hide_sal = hide_sal




    @api.constrains('social_security_number')
    def check_social_security_number(self):
        """
        This method will check the social security number whether it's a digit or not.
        ------------------------------------------------------------------------------
        @param self: object pointer
        """
        for emp in self:
            if emp.social_security_number and not emp.social_security_number.isdigit():
                raise ValidationError(_('The Social Security Number should be digits only!'))

    @api.constrains('health_insurance_card_number')
    def check_health_insurance_card_number(self):
        """
        This method will check the social security number whether it's a digit or not.
        ------------------------------------------------------------------------------
        @param self: object pointer
        """
        for emp in self:
            if emp.health_insurance_card_number and not emp.health_insurance_card_number.isdigit():
                raise ValidationError(_('The Health Insurance Card Number should be digits only!'))

    @api.constrains('incoming_no')
    def check_incoming_number(self):
        """
        This method will check the social security number whether it's a digit or not.
        ------------------------------------------------------------------------------
        @param self: object pointer
        """
        for emp in self:
            if emp.incoming_no and not emp.incoming_no.isdigit():
                raise ValidationError(_('The Incoming Number should be digits only!'))

    def _cron_add_schedule_time(self):
        """
        This is a scheduler method which will be called on a time interval to add a line in Schedule Time
        -------------------------------------------------------------------------------------------------
        :param self: object pointer
        """
        emp_obj = self.env['hr.employee']
        employees = emp_obj.search([])
        for employee in employees:
            schedule = self.env['schedule.time'].search([('employee_id', '=', employee.id),
                                                             ('from_date', '=', 0),
                                                             ('to_date', '=', 0)], limit=1)
            if not schedule.id and employee.department_id and employee.department_id.working_schedule_id:
                employee.schedule_time_ids = [(0, 0, {'from_date': 0,
                                                      'to_date': 0,
                                                      'working_schedule_id': employee.department_id.working_schedule_id.id
                                                      })]

    @api.onchange('department_id')
    def _onchange_department(self):
        """
        This method will update the working hours of employee
        -----------------------------------------------------
        @param self: object pointer
        """
        flag = True
        super(Employee, self)._onchange_department()
        for emp in self:
            if emp.department_id:
                emp.resource_calendar_id = emp.department_id.working_schedule_id
                emp.leave_manager_id = emp.department_id.manager_id.user_id.id
            else:
                emp.resource_calendar_id

            for schedule_time in emp.schedule_time_ids:
                if schedule_time.from_date == 0 and schedule_time.to_date == 0:
                    flag = False
                    schedule_time.working_schedule_id = emp.department_id.working_schedule_id.id
            if flag:
                emp.schedule_time_ids = [(0, 0, {'from_date': 0,
                                                 'to_date': 0,
                                                 'working_schedule_id': emp.department_id.working_schedule_id.id})]


    @api.depends('name', 'middle_name', 'last_name', 'fourth_name')
    def _compute_display_name(self):
        for emp in self:
            emp.display_name = "%s %s %s %s" %(ustr(emp.name or ""), ustr(emp.middle_name or ""), ustr(emp.last_name or ""), ustr(emp.fourth_name or ""))
            emp.user_id.partner_id.name = emp.display_name

    @api.depends('first_name_arabic', 'middle_name_arabic', 'last_name_arabic', 'fourth_name_arabic')
    def _compute_employee_name_arabic(self):
        for emp in self:
            emp.full_name_arabic = str(emp.first_name_arabic) + " " + str(emp.middle_name_arabic) + " " + str(emp.last_name_arabic) + " " + str(emp.fourth_name_arabic)

    @api.constrains('passport_id', 'national_id')
    def check_passport_id_national_id(self):
        passports = self.env['hr.employee'].search([('passport_id', '=', self.passport_id), ('id', '!=', self.id)])
        nationals = self.env['hr.employee'].search([('national_id', '=', self.national_id), ('id', '!=', self.id)])

        for emp in self:
            if not emp.national_id and not emp.passport_id:
                raise ValidationError(_('Please Fill Either National ID or Passport No'))

        for passport in passports:
            for national in nationals:
                if passport.passport_id and national.national_id:
                    raise ValidationError(_("An employee with the following National ID/Passport Number '%s' / '%s' exists.") % (
                        self.passport_id , self.national_id,))
        for passport in passports:
            if passport.passport_id:
                raise ValidationError(_("An employee with the following Passport Number '%s' ' exists.") % (
                        self.passport_id,))
        for national in nationals:
            if national.national_id:
                raise ValidationError(_("An employee with the following National ID '%s' exists.") % (
                        self.national_id,))

    @api.model
    def create(self, vals):
        vals.update({'display_name': "%s %s %s %s" % (
            ustr(vals.get('name', '')), ustr(vals.get('middle_name', '')), ustr(vals.get('last_name', '')),
            ustr(vals.get('fourth_name', '')))})
        res = super(Employee, self).create(vals)
        res.user_id.partner_id.name = vals['display_name']
        if res.job_id:
            self.env['job.history.line'].create({
                'new_job_position': res.job_id.id,
                'changing_date': res.starting_date or False,
                'history_id': res.id,
                'status': 'promotion',
            })

        scheduler_id = res.department_id.working_schedule_id.id
        if self._context and self._context.get('applications'):
            scheduler_id = self._context.get('applications')

        res.schedule_time_ids = [(0, 0, {'from_date': 0, 'to_date': 0,
                                         'working_schedule_id': scheduler_id})]
        return res


    mark_absence = fields.Boolean(string='Absence')
    mark_check_in = fields.Boolean(string='Check in')
    mark_check_out = fields.Boolean(string='Check out')
    mark_permissions = fields.Boolean(string='Permissions')
    mark_breastfeeding = fields.Boolean(string='Breastfeeding Hour')
    mark_educational = fields.Boolean(string='Educational')
    mark_attending_weekends = fields.Boolean(string='Attending Weekends')
    mark_other = fields.Boolean(string='Other')

    sat_absence = fields.Boolean()
    sat_check_in = fields.Boolean()
    sat_check_out = fields.Boolean()
    sat_permissions = fields.Boolean()
    sat_breastfeeding = fields.Boolean()
    sat_educational = fields.Boolean()

    sun_absence = fields.Boolean()
    sun_check_in = fields.Boolean()
    sun_check_out = fields.Boolean()
    sun_permissions = fields.Boolean()
    sun_breastfeeding = fields.Boolean()
    sun_educational = fields.Boolean()

    mon_absence = fields.Boolean()
    mon_check_in = fields.Boolean()
    mon_check_out = fields.Boolean()
    mon_permissions = fields.Boolean()
    mon_breastfeeding = fields.Boolean()
    mon_educational = fields.Boolean()

    tue_absence = fields.Boolean()
    tue_check_in = fields.Boolean()
    tue_check_out = fields.Boolean()
    tue_permissions = fields.Boolean()
    tue_breastfeeding = fields.Boolean()
    tue_educational = fields.Boolean()

    wed_absence = fields.Boolean()
    wed_check_in = fields.Boolean()
    wed_check_out = fields.Boolean()
    wed_permissions = fields.Boolean()
    wed_breastfeeding = fields.Boolean()
    wed_educational = fields.Boolean()

    thu_absence = fields.Boolean()
    thu_check_in = fields.Boolean()
    thu_check_out = fields.Boolean()
    thu_permissions = fields.Boolean()
    thu_breastfeeding = fields.Boolean()
    thu_educational = fields.Boolean()

    deduction_absence = fields.Boolean()
    deduction_check_in = fields.Boolean()
    deduction_check_out = fields.Boolean()
    deduction_permissions = fields.Boolean()
    deduction_breastfeeding = fields.Boolean()
    deduction_educational = fields.Boolean()

    check_in_absence = fields.Float()
    check_in_check_in = fields.Float()
    check_in_check_out = fields.Float()
    check_in_permissions = fields.Float()
    check_in_breastfeeding = fields.Float()
    check_in_educational = fields.Float()
    check_in_attending_weekends = fields.Float()

    check_out_absence = fields.Float()
    check_out_check_in = fields.Float()
    check_out_check_out = fields.Float()
    check_out_permissions = fields.Float()
    check_out_breastfeeding = fields.Float()
    check_out_educational = fields.Float()
    check_out_attending_weekends = fields.Float()

    note_absence = fields.Text()
    note_check_in = fields.Text()
    note_check_out = fields.Text()
    note_permissions = fields.Text()
    note_breastfeeding = fields.Text()
    note_educational = fields.Text()
    note_attending_weekends = fields.Text()

    friday_attending_weekends = fields.Boolean(string='Friday')
    saturday_attending_weekends = fields.Boolean(string='Saturday')

    note_other = fields.Text()


class JobHistory(models.Model):
    _name = 'job.history.line'
    _description = 'Job History Model'

    history_id = fields.Many2one('hr.employee','History')
    new_job_position = fields.Many2one('hr.job', string="New Job Position")
    changing_date = fields.Date(string='Changing Date')
    status = fields.Selection([('promotion', 'Promotion'), ('demotion', 'Demotion')], 'Status')


class ScheduleTime(models.Model):
    _name = 'schedule.time'
    _description = 'Schedule Time'

    from_date = fields.Integer("From", limit=2)
    to_date = fields.Integer("To", limit=2)
    employee_id = fields.Many2one('hr.employee', string="Employee")
    working_schedule_id = fields.Many2one('resource.calendar',string="Working Schedule")










