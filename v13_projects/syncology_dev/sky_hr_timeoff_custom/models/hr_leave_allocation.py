from odoo import models, fields, api, _


class LeaveAllocation(models.Model):
    _inherit = 'hr.leave.allocation'
    _description = 'Hr Leave Allocation'

    @api.depends('employee_id.first_name_arabic', 'employee_id.middle_name_arabic', 'employee_id.last_name_arabic', 'employee_id.fourth_name_arabic')
    def _compute_employee_name_arabic(self):
        for allocation in self:
            allocation.employee_arabic_name = str(allocation.employee_id.first_name_arabic) + " " + str(allocation.employee_id.middle_name_arabic) + " " + str(allocation.employee_id.last_name_arabic) + " " + str(allocation.employee_id.fourth_name_arabic)

    employee_arabic_name = fields.Char('Employee (Arabic)', compute="_compute_employee_name_arabic", tracking=True, store=True)
    holiday_status_id = fields.Many2one(
        "hr.leave.type", string="Leave Type", readonly=True,
        states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]})
    leave_type = fields.Selection([('vacation', 'Vacation'),
                                   ('leave', 'Leave')], 'Leave Type')
    type_request_unit = fields.Selection(related='holiday_status_id.request_unit', store=True)
    number_of_days = fields.Integer('Number of Days',
                                    tracking=True,
                                    default=1,
                                    help='Duration in days. Reference field to use when necessary.')
    number_of_days_display = fields.Integer('Duration (days)',
                                            compute='_compute_number_of_days_display',
                                            states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]},
        help="If Accrual Allocation: Number of days allocated in addition to the ones you will get via the accrual' system.")
    emp_parent_id = fields.Many2one('hr.employee', 'Manager', related='employee_id.parent_id', store=True)
    job_id = fields.Many2one('hr.job', string='Job', related='employee_id.job_id', store=True)

    def init(self):
        self.env.cr.execute("select conname from pg_constraint where conname='hr_leave_allocation_duration_check'")
        result = self.env.cr.fetchone()
        if result:
            self.env.cr.execute("ALTER TABLE hr_leave_allocation DROP CONSTRAINT hr_leave_allocation_duration_check;")

    @api.model
    def default_get(self, fields):
        res = super(LeaveAllocation, self).default_get(fields)
        if res.get('holiday_status_id', False):
            del res['holiday_status_id']
        return res

    def name_get(self):
        """
        The overridden method to set display_name
        -----------------------------------------
        @param self: object pointer
        """
        res = []
        for allocation in self:
            if allocation.holiday_type == 'company':
                target = allocation.mode_company_id.name
            elif allocation.holiday_type == 'department':
                target = allocation.department_id.name
            elif allocation.holiday_type == 'category':
                target = allocation.category_id.name
            else:
                target = allocation.employee_id.sudo().name

            if allocation.type_request_unit == 'hour':
                res.append(
                    (allocation.id,
                     _("Allocation of %d hour(s) to %s") % (
                        allocation.number_of_hours_display,
                        target)
                    )
                )
            else:
                res.append(
                    (allocation.id,
                     _("Allocation of %d day(s) to '%s'") % (
                        allocation.number_of_days,
                        target)
                    )
                )
        return res

    @api.onchange('number_of_hours_display')
    def _onchange_number_of_hours_display(self):
        self.number_of_days = self.number_of_hours_display

    @api.depends('number_of_days', 'employee_id')
    def _compute_number_of_hours_display(self):
        for allocation in self:
            allocation.number_of_hours_display = allocation.number_of_days