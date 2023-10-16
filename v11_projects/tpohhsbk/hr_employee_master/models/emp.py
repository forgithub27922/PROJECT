from odoo import api,models,fields,_

class Emp(models.Model):

    _inherit = "hr.employee"

    #display this field in form view
    alt_id = fields.Char(string="Alt.ID")
    emp_type_id = fields.Many2one('employee.type','Employee Type')
    category_id = fields.Many2one('emp.category','Category')
    personal_id = fields.Char('Personal ID')
    sponser_id = fields.Many2one('emp.sponser','Sponser')
    pay_group_id = fields.Many2one('emp.pay.group','Pay Group')

    # display this fields in office details tab in form view
    position_cat_id = fields.Many2one('position.cat','Position Cat')
    sub_department_id = fields.Many2one('hr.department','Sub-Dept.')
    location_id = fields.Many2one('emp.location','Location')
    branch_id = fields.Many2one('emp.branch','Branch')
    join_date = fields.Date('Join Date')
    eos_eff_date = fields.Date('EOS Eff. Date')
    probation_period = fields.Integer('Probation Period')
    division_id = fields.Many2one('emp.division','Divison')
    seniority_date = fields.Date('Seniority Date')
    complete_on = fields.Date('Complete on')
    rejoin_date = fields.Date('Rejoin Date')
    exit_date = fields.Date('Exit Date')

    # display this fields in private info tab in form view
    wedding_date = fields.Date('Wedding Date')
    religion = fields.Char('Religion')
    blood_group = fields.Selection([('a+','A+'),('a-','A-'),('ab+','AB+'),
                                    ('ab-','AB-'),('o+','O+'),('o-','O-'),
                                    ('b+', 'B+'), ('b-', 'B-')],'Blood Group')

    visa_status = fields.Many2one('visa.status','Visa Status')

    bank_name = fields.Char('Bank Name')
    iban_no = fields.Char('IBAN No.')
    account_name = fields.Char('Account Name')
    amount = fields.Float('Amount')

    # display this field in contact tab in form view
    partner_ids = fields.One2many('res.partner','employee_id','Partner')

    # display this fields in other info tab in form view
    is_insurance = fields.Boolean('Is Insurance')
    policy_no = fields.Char('Policy No.')
    company = fields.Many2one('res.company','Company')
    category = fields.Many2one('insurance.category','Category')
    insured_from = fields.Date('Insured From')
    insured_to = fields.Date('Insured To')
    insurance_amount = fields.Float('Insurance Amount')
    premium = fields.Float('Primium')

    document = fields.Binary('Attachment')
    document_no = fields.Char('Document No.')
    document_type = fields.Char('Document Type')
    issue_date = fields.Date('Issue Date')
    exp_date = fields.Date('Expiry Date')
    issue_place = fields.Char('Place Of Isuue')
    issued_by = fields.Char('Issue By')
    reminder_date = fields.Date('Reminder Date')

    # display this field in education tab in form view
    education_ids = fields.One2many('employee.education','employee_id','Education Details')

    # display this field in experience tab in form view
    experience_ids = fields.One2many('employee.experience','employee_id','Experience')

    # display this field in Assets tab in form view
    asset_ids = fields.One2many('emp.asset', 'employee_id','Assets')

class Emp_Type(models.Model):
    _name = 'employee.type'

    name = fields.Char('Name')


class Emp_Category(models.Model):
    _name = "emp.category"

    name = fields.Char('Name')

class Position_cat(models.Model):
    _name = "position.cat"

    name = fields.Char('name')

class Emp_Location(models.Model):
    _name="emp.location"

    name=fields.Char('name')


class Emp_Branch(models.Model):
    _name = "emp.branch"

    name = fields.Char('name')


class Emp_Divison(models.Model):
    _name = "emp.division"

    name = fields.Char('name')


class Emp_sponser(models.Model):
    _name = "emp.sponser"

    name = fields.Char('name')

class Emp_Pay_Group(models.Model):
    _name = "emp.pay.group"

    name = fields.Char('name')

class Visa_Status(models.Model):
    _name="visa.status"

    name = fields.Char('name')


class Contact(models.Model):
    _inherit = "res.partner"
    # override this field
    company_type = fields.Selection(string='Company Type',
                                    selection=[('person', 'Individual'),
                                               ('company', 'Company'),
                                               ('dependent', 'Dependent')],
                                    compute='_compute_company_type',
                                    inverse='_write_company_type')
    is_person = fields.Boolean('is Person')
    employee_id = fields.Many2one('hr.employee','Employee')
    address_type = fields.Char('Address Type')


    @api.depends('is_company', 'is_person')
    def _compute_company_type(self):
        for partner in self:
            if partner.is_company:
                partner.company_type = 'company'
            elif partner.is_person:
                partner.company_type = 'person'
            else:
                partner.company_type = 'dependent'

    def _write_company_type(self):
        for partner in self:
            if partner.company_type == 'company':
                partner.is_company = True
            elif partner.company_type == 'person':
                partner.is_person = True
            else:
                partner.is_person = False
                partner.is_company = False

    @api.onchange('company_type')
    def onchange_company_type(self):
        if self.company_type == 'company':
            self.is_company = (self.company_type == 'company')
            self.is_person = False
        elif self.company_type == 'person':
            self.is_company = False
            self.is_person = True
        else:
            self.is_person = False
            self.is_company = False


class Education(models.Model):
    _name = 'employee.education'

    employee_id = fields.Many2one('hr.employee','Employee Name')
    education_id = fields.Many2one('education.name','Education')
    type = fields.Selection([('tech','Technical'),('non_tech','Non Technical')])
    university_id = fields.Many2one('education.university','University')
    country_id = fields.Many2one('res.country','Country')
    grade = fields.Char('Mark/Grade')
    year = fields.Char('Year')


class Experience(models.Model):
    _name = 'employee.experience'

    employee_id = fields.Many2one('hr.employee','Employee Name')
    designation = fields.Char('Designation')
    company_id = fields.Many2one('res.company','Company')
    country_id = fields.Many2one('res.country','Country')
    peroid_from = fields.Date('Period From')
    peroid_to = fields.Date('Period To')
    reference = fields.Text('Reference')

class Insurance_Category(models.Model):
    _name = 'insurance.category'

    name = fields.Char('Category Name')

class Education_Name(models.Model):
    _name = 'education.name'

    name = fields.Char('Education Name')

class Education_University(models.Model):
    _name= 'education.university'

    name= fields.Char('University Name')


class Assets(models.Model):
    _name = 'emp.asset'

    name = fields.Char('Assets Name')
    asset_no = fields.Char('Assets No.')
    details = fields.Text('Details')
    issue_date = fields.Date('Issue Date')
    return_date = fields.Date('Return Date')
    employee_id = fields.Many2one('hr.employee','Employee')
    department_id = fields.Many2one('hr.department','Department')
    location_id = fields.Many2one('emp.location','Location')
    division_id = fields.Many2one('emp.division','division')


