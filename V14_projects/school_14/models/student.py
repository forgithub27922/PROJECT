from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


# odoo = directory
# models = models.py file inside odoo directory
# fields = fields.py file inside odoo directory
# api = api.py file inside odoo directory
# exceptions = exceptions.py file inside odoo directory

# models.Model = class defined inside models.py file which will be parent of all models.
class Student(models.Model):
    # _name = Model Attribute which will be the technical name of the models
    # It will be used at multiple places to refer to this models be it views, actions, other models, relational fields, access rights, reports etc.
    # A table will be created in the database with this name where the '.' will be replaced by '_' if existing in the given name.
    # For e.g. in our case the models 'student.student' will be mapped to the table 'student_student'
    _name = 'student.student'

    # _description = The fucntional name for the models student.student
    _description = 'Students'

    # This will be the name of the table if given it will create the table with this name.
    # If not given it will take the name as mentioned above on the _name attribute description.
    _table = 'school_student'

    # this is the models attribute which forces the auto creation of the table from models
    # Default value is True.
    # In case you give False you will have to override the init() method and create the table manually
    _auto = True

    # this is the order in which the records will be displayed on the view or fetched during the methods.
    # you can give field name(s) and then if you want to have descending order you can postfix the field by 'desc'
    # _order = 'name desc'
    _order = 'sequence'  # When using handle widget

    # Used for Hierarchy and searching by parent_of and child_of operators
    _parent_name = 'parent_id'
    # This will be used to store the parent_path and it will be helpful in searching all the parents or children of a node.
    _parent_store = True

    # This constraints will be added on the table of the models for the fields mentioned on the constraints
    # Here you would list out all your constraints that you want to add on your table.
    # Only Unique and Check constraints will be used here as other are already being managed.
    # Primary key = By default as id field
    # Foreign Key = Many2one field
    # Not Null = required attribute
    # The _sql_constraints is a list of tuple where each tuple is a single constraint.
    # The tuple contains exactly 3 elements, name, constraints and a message.
    _sql_constraints = [
        ('unique_roll_no', 'unique(roll_no)', 'The roll no of the student must be unique!'),
        ('check_age', 'check(age>6)', 'The Student must be at least 6 years old!')
    ]

    # Fields Syntax
    # <field_name> = fields.<Data Type>(params)

    # Pre-defined Fields
    # These field are automatically created in the table of the models we don't create it in our models
    # These are also called Magic Fields
    # id - Primary Key (Creates a sequence which will automatically generate the next id)
    # create_date - The timestamp(datetime) when the record was created
    # create_uid - The id of the user who created this record (foreign key - res.users)
    # write_date - The timestamp(datetime) when the record was last edited
    # write_uid - The id of the user who updated the record lastly (foreign key - res.users)

    # Character Field
    # string will be the label of the field common for all the fields.
    # required will make the field mandatory and will also add a not null constraint in the database table on this field common for all the fields.
    # index will be used to create an index on the database table for this field. common for searchable field. use it only on most searched field.
    # translate will be used only for Char, Text and Html field. It will translate the fields in to other languages.
    # trim will be used for trimming the space on the string from both the sides, used with Char field.
    name = fields.Char(string='Name', required=True, index=True, translate=True, trim=True)

    # Integer Field
    # Using group_operator you can display this amount on the groups.
    # There are multiple options like sum, avg, min and max.
    # By default it is sum always
    # age = fields.Integer('Age', group_operator='sum') # Default
    # group_operator is an attribute which is used when you group the records on the list view.
    # The numeric fields such as float or integer has the impact.
    # sum is the default value for group_operator.
    # you can use avg, min, max apart from sum.
    age = fields.Integer('Age', group_operator='avg')
    # age = fields.Integer('Age', group_operator='min')
    # age = fields.Integer('Age', group_operator='max')

    # Float Field
    # default is used to provide the default value, common for all fields.
    # digits is used to set the fractional digits or decimal precision on the fields. Here we have used 3 so it will set 3 digits after the decimal point
    # fee = fields.Float('Fee', readonly=True, default=200.0, digits=(16, 3))
    fee = fields.Float('Fee', default=200.0, digits=(16, 3))

    # Boolean Field
    active = fields.Boolean('Active', default=True)

    # Text Field
    notes = fields.Text('Notes')

    # Html Field
    # groups are used to give access to specific group to view this field. Means only the users of this group will see this field
    comments = fields.Html('Comments', groups='school_14.grp_school_admin')

    # Date Field
    # In case of current date always use the today() method from fields.Date class. You can set it as default as well.
    birthdate = fields.Date('BirthDate', help='This is the date of birth of student', default=fields.Date.today())

    # Datetime Field
    # In case of current timestamp always use the now() method from fields.Datetime class. You can set it as default as well.
    first_attendance = fields.Datetime('First Attendance', default=fields.Datetime.now())
    last_attendance = fields.Datetime('Last Attendance')

    # Selection Field
    # Here the first param is the selection which is consisting of a list of tuple.
    # Each tuple has exactly 2 elements.
    # The first one will be stored in the database and the second one will be displayed in the view.
    # The second parameter is label
    gender = fields.Selection(selection=[('male', 'Male'), ('female', 'Female')], string='Gender')

    # You can use the size field to restrict the maximum no of characters in a Character Field.
    student_code = fields.Char('Student Code', size=64)
    password = fields.Char('Password')
    email = fields.Char('Email')
    url = fields.Char('URL')
    phone = fields.Char('Phone No')

    # With priority field the keys must be always either numbers starting from 0 or alphabetic from a to z.
    # If used a string starting with same alphabet will be considered as same value.
    priority = fields.Selection([(str(ele), str(ele)) for ele in range(6)], 'Priority')
    school_hours = fields.Float('School Hours')
    shift = fields.Selection([('morning', 'Morning'), ('afternoon', 'Afternoon')], 'Shift')

    # Relational Fields
    # All relational fields will have first parameter as a models (comodel_name)
    # this will be the models with which we are creating a relation.
    # Many2one field (2 params, 1 models, 2 label)
    standard_id = fields.Many2one('school.standard', 'Standard')

    # One2many field (3 params 1 models, 2 inverse field, 3 label)
    # The inverse field must be a many2one field in the comodel for the current models.
    # In our case there must be a student_id many2one field of student.student in student.marks models
    # marks_ids = fields.One2many('student.marks', 'student_id', 'Marks', limit=2)
    # copy is a parameter which is used on duplication.
    # when you duplicate a record all the fields which have copy=True will be copied.
    # By default all fields except one2many have copy=True. O2M has copy=False
    marks_ids = fields.One2many('student.marks', 'student_id', 'Marks', copy=True)

    # Many2many field (2 / 5 params)
    # Option 1 2 params (comodel_name, label)
    # In case you don't want a field to be copied on the duplicated record, you can use copy=False
    activity_ids = fields.Many2many('student.activity', string='Activities', copy=False)
    # activity_ids = fields.Many2many('student.activity', string='Activities', limit=3)
    # Option 2 5 params (comodel_name, 'look_up_table', 'id_of_cur_model', 'id_of_comodel', label)
    # activity_ids = fields.Many2many('student.activity', 'std_act_rel', 'student_id', 'activity_id', 'Activities')

    # Reference Field
    # This is a combination of Selection and Many2one fields
    # This has 2 parameters 1 selection of models, 2 string
    # the first element of the tuple must be a models name
    ref = fields.Reference([('res.partner', 'Partner'), ('res.users', 'Users'), ('student.student', 'Student')],
                           'Reference')

    # Other Fields
    # Monetary Field
    # It must have a many2one field for currency(res.currency)
    # 2 params 1 currency_field, 2 String / Label
    currency_id = fields.Many2one('res.currency', 'Currency')
    annual_fees = fields.Monetary(currency_field='currency_id', string='Annual Fees')

    # Binary Field
    doc = fields.Binary('Document')
    # The field used to store the name of the file selected in doc field.
    file_name = fields.Char('File Name')

    # Image Field
    image = fields.Binary('Image')

    # Compute Field from another models
    # compute's value will be a method which will be used to compute the value of this field.
    # compute field are not stored in the database.
    # Ths compute method is called when you save / read a record.
    total_marks = fields.Float('Total Marks', compute='_calc_total_marks')
    total_obt_marks = fields.Float('Total Obt. Marks', compute='_calc_total_marks')
    # You can forcefully store a compute field in database by giving store=True
    percentage = fields.Float('Percentage', compute='_calc_perc', store=True)

    # Related Field (M2O)
    std_code = fields.Char('Standard Code', related='standard_id.code')

    # Reserved Field : state
    state = fields.Selection([('draft', 'Applied'),
                              ('interviewed', 'Interviewed'),
                              ('rejected', 'Rejected'),
                              ('accepted', 'Accepted'),
                              ('joined', 'Joined'),
                              ('left', 'Left')], 'State', default='draft')

    # Reserved Field : sequence
    sequence = fields.Integer('Sequence')

    # Reserved Field : parent_id  Hierarchy
    parent_id = fields.Many2one('student.student', 'Monitor')
    child_ids = fields.One2many('student.student', 'parent_id', 'Students')
    # Reserved Field : parent_path
    parent_path = fields.Char('Parent Path', index=True)
    # Reserved Field : company_id
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company.id)

    no_of_marks = fields.Float('#Marks', compute='_count_marks')

    roll_no = fields.Integer('roll_no')

    color = fields.Integer('Color Index')

    def _count_marks(self):
        """
        This method will count the no of records for marks
        --------------------------------------------------
        @param self: object pointer
        """
        mark_obj = self.env['student.marks']
        for stud in self:
            stud.no_of_marks = mark_obj.search_count([('student_id', '=', stud.id)])

    # If you want to compute the value dynamically on the spot when you change values of fields
    # on which our field is being computed from then you will have to put those fields in depends.
    # Whenever you will change the fields mentioned in depends your compute field will be automatically calculated.
    # NOTE : If you have store=True then @depends is a must else the value will never be calculated.
    @api.depends('marks_ids')
    def _calc_total_marks(self):
        """
        This method will calcualte the total of total marks and obtained marks
        ----------------------------------------------------------------------
        @param self: object pointer
        """
        for stud in self:
            # stud.total_marks = 0.0
            # stud.total_obt_marks = 0.0
            # M2O field will again give you a recordset with one record.
            # print("STANDARD", stud.standard_id)
            # O2M field will give you a recordset with one or more records.
            # print("MARKSSSSSSSSSSSSS", stud.marks_ids)
            # M2M field will give you a recordset with one or more records.
            # print("ACTIVTITIES", stud.activity_ids)
            # Reference field will again give you a recordset with one record.
            # print("REF", stud.ref)
            total = 0.0
            total_obt = 0.0
            for marks in stud.marks_ids:
                total += marks.total_marks
                total_obt += marks.obt_marks
            # So when a method assigns multiple fields it means the same method is used in the compute of multiple fields.
            stud.total_marks = total
            stud.total_obt_marks = total_obt

    @api.depends('total_marks', 'total_obt_marks', 'marks_ids')
    def _calc_perc(self):
        """
        This method will calculate the percentage from calculated total marks and obtained marks
        ----------------------------------------------------------------------------------------
        @param self: object pointer
        """
        for stud in self:
            # perc = 0.0
            # if stud.total_marks:
            #     perc = stud.total_obt_marks * 100 / stud.total_marks
            # stud.percentage = perc
            stud.percentage = stud.total_marks and ((stud.total_obt_marks * 100 / stud.total_marks) > 60.0 and (
                    stud.total_obt_marks * 100 / stud.total_marks) or 0.0) or 0.0

    def stud_interviewed(self):
        # This is s a button method which will be called when you will click the Interviewed button.
        """
        This method will change the state of the student to interviewed.
        ----------------------------------------------------------------
        @param self: object pointer
        """
        for emp in self:
            emp.state = 'interviewed'

    def stud_accept(self):
        """
        This method will change the state of the student to accepted.
        -------------------------------------------------------------
        @param self: object pointer
        """
        # The attributes of self.
        # self._context is a dictionary which flows through the environment and can be used to pass special values.
        # It already contains information which are relevant to the system and user.
        # print("CTX", self._context)
        # self._cr is the cursor which can be used to execute queries.
        # print("CR", self._cr)
        # self._uid is the current logged in user.
        # print("UID", self._uid)

        # self.env is the Environment object.
        # In environment all the models are being registered.
        # it is derived from dictionary class and has some method similar to dictionary.
        # print("ENV", self.env)

        # It can be used to fetch an object / blank recordset.
        # std_obj = self.env['school.standard']
        # print("STD OBJ", std_obj)

        # args will return 4 things.
        # 1. db cursor, uid, context and False.
        # print("ARGS", self.env.args)

        # You can get cr, uid, context from environment object as well
        # print("CR1", self.env.cr)
        # print("CR1", self.env.uid)
        # print("CTX1", self.env.context)

        # You can get the recordset of the current logged in user.
        # print("User", self.env.user)

        # The company will be the current company on which the user is workimg or is selected on the top toolbar.
        # print("User", self.env.company)

        # The comapnies will be all the companies which are selected with a checkbox on the company selection widget.
        # print("User", self.env.companies)

        # This is the language of the logged in user
        # print("User", self.env.lang)

        # print(dir(self.env))
        # print(self.env.get('ir.ui.view'))

        # ref() method of environment is used to get a recordset of the given xml id.
        # The xmlid must be given prefixed by module name and a dot('.').
        # The mapping of xmld id and actual id(Primary Key) of the record is done in the models ir.models.data.
        # The table will be ir_model_data where the information is stored.
        # It has fields like id, name, models, module, res_id.
        # Here name is the xml id and res_id is the id(Primary Key) of the actual record.
        # view = self.env.ref('school_14.view_marks_form')
        # print("VIEW", view)
        # acc = self.env.ref('school_14.access_standard_admin')
        # print("ACCESS", acc)

        # We can also use the dictonary methods keys(), values() and items().
        # keys() will give you a list of all the models.
        # print(list(self.env.keys()))
        # values() will give you list of all models's objects / blank recordsets.
        # print(list(self.env.values()))
        # items() will give you a list of tuple where first element will be models and second one models's object.
        # print(list(self.env.items()))
        for emp in self:
            emp.state = 'accepted'

    def stud_reject(self):
        """
        This method will change the state of the student to rejected.
        -------------------------------------------------------- ----
        @param self: object pointer
        """
        # print("SELF", self)
        # # Removing the deleted records from cache
        # res = self.exists()
        # print(res)
        # mark_obj = self.env['student.marks']
        # res = mark_obj.exists()
        # print(res)

        # If there is one record it will not do anything.
        # If theer is more or less than it will raise an error of Expected Singleton
        # self.ensure_one()
        # # mark_obj.ensure_one() #ERROR : Expected Singleton

        # This will give you a dictionary containing the 5 predefined fields for the record for which you're calling the method, also xmlid as well.
        # res = self.get_metadata()
        # print("RES", res)
        # view = self.env.ref('school_14.view_marks_form')
        # res = view.get_metadata()
        # print(res)

        # studs = self.search(['|', ('active', '=', True), ('active', '=', False)])
        # print(studs)
        # marks = mark_obj.search([])
        # print(marks)

        # filtered() is a method of recordset which is used to filter the records.
        # there are two ways to use it.
        # 1. <recordset>.filtered('<field_name>')
        # Here it will check whether the field has a value or not.
        # active_studs = studs.filtered('active')
        # print("ACTIVE STUDS", active_studs)
        # std_studs = studs.filtered('standard_id')
        # print("STANDARD STUDS", std_studs)
        # 2. <recordset>.filtered(lambda r: r.<field_name> <operator> <value>)
        # Here it will compare the value given explicitly and filter those records.
        # male_studs = studs.filtered(lambda r: r.gender == 'male')
        # print("MALE", male_studs)
        # female_studs = studs.filtered(lambda r: r.gender == 'female')
        # print("FEMALE", female_studs)
        #
        # res = marks.filtered(lambda r: r.obt_marks > 60.0)
        # print(res)
        # res = marks.filtered(lambda r: r.obt_marks < 60.0)
        # print(res)

        # mapped is another method of recordset which is used to get the field values for multiple records or perforom some operation on the value.
        # It returns a list.
        # 1. <recordset>.mapped('<field_name>')
        # You can directly get a list of fields' values for passed records.
        # res = studs.mapped('name')
        # print(res)
        # 2. <recordset>.mapped(lambda r: <expression>)
        # Here the result of the expression will be stored in the list for all the records.
        # res = studs.mapped(lambda r: r.name)
        # print(res)
        #
        # res_total_marks = marks.mapped('total_marks')
        # print("TOTAL", res_total_marks)
        # res_obt_marks = marks.mapped(lambda r: r.obt_marks)
        # print("OBT", res_obt_marks)
        # failed = []
        # for ele in res_obt_marks:
        #     if ele < 60.0:
        #         failed.append(ele)
        # print("FAILED", failed)
        # failed = [ele for ele in res_obt_marks if ele < 60.0]
        # print("FAILED", failed)
        # failed = filter(lambda ele: ele < 60, res_obt_marks)
        # print(failed)
        #
        # res_obt_marks = marks.mapped(lambda r: (r.student_id.name, r.obt_marks))
        # print("OBT", res_obt_marks)
        #
        # res_total_marks = sum(marks.mapped('total_marks'))
        # print("TOTAL", res_total_marks)
        # res_obt_marks = sum(marks.mapped(lambda r: r.obt_marks))
        # print("OBT", res_obt_marks)
        #

        # sorted is a method of recordset which is used to sort the record by fields.
        # for descending order you can user reverse=True as second parameter.
        # # studs1 = studs.sorted('name')
        # # print(studs1)
        #
        # studs2 = studs.sorted('name', reverse=True)
        # print(studs2)
        #
        # studs3 = studs.sorted(lambda r: r.id, reverse=True)
        # print(studs3)

        studs_all = self.search([])
        studs_few = self.search([('id', 'in', [1, 3, 4, 5, 6])])
        studs_few2 = self.search([('id', 'in', [3, 4, 7, 8, 9])])
        studs_mny = self.search([('id', 'in', [1, 3, 4, 5, 6, 7, 8, 9])])

        print("ALL", studs_all)
        print("FEW", studs_few)
        print("MANY", studs_mny)
        print("FEW2", studs_few2)
        # if self in studs_all:
        #     print("YES", self)
        #
        # if self not in studs_few:
        #     print("NOT IN", self)
        #
        # Checking subset of a recordset
        # print(studs_all < studs_few)

        # Checking superset of a recordset
        # print(studs_all > studs_few)

        # Union operation between two recordsets
        un_studs = studs_few | studs_few2
        print(un_studs)

        # Intersection operation between two recordsets
        in_studs = studs_few & studs_few2
        print(in_studs)

        # Difference operation between two recordsets
        diff_studs = studs_few - studs_few2
        print(diff_studs)

        # for emp in self:
        #     emp.state = 'rejected'

    def stud_join(self):
        """
        This method will change the state of the student to joined.
        -----------------------------------------------------------
        @param self: object pointer
        """
        for emp in self:
            emp.state = 'joined'

    def stud_leave(self):
        """
        This method will change the state of the student to left.
        ---------------------------------------------------------
        @param self: object pointer
        """
        for emp in self:
            emp.state = 'left'

    def create_record(self):
        """
        This method is a button's method which will be called when you click the button.
        Used to test the create method to create records
        --------------------------------------------------------------------------------
        @param self: object pointer
        """
        # Create method is used to create a record set.
        # @api.model_create_multi
        # def create(self, vals_lst):
        # @param self: object pointer
        # @param vals_lst : list of dictionaries which contain fields and their respective values.
        # returns a record set of newly created record(s)
        # emp_vals = {
        #     'name': 'Abhinav Bindra',
        #     'age': 38,
        #     'fee': 450.0,
        #     'active': True,
        #     'gender': 'male',
        #     'birthdate': fields.Date.today(),
        #     'first_attendance': fields.Datetime.now(),
        #     'standard_id': 1,
        #     'marks_ids': [
        #         (0, 0, {
        #             'subject': 'Physics',
        #             'total_marks': 100.0,
        #             'obt_marks': 85.0
        #         }),
        #         (0, 0, {
        #             'subject': 'Chemistry',
        #             'total_marks': 100.0,
        #             'obt_marks': 82.0
        #         }),
        #         (0, 0, {
        #             'subject': 'Maths',
        #             'total_marks': 100.0,
        #             'obt_marks': 90.0
        #         })
        #     ],
        #     'activity_ids': [(4, 1), (4, 4), (4, 7)],
        #     # 'activity_ids': [(6, 0, [1, 4, 7])]
        # }
        # emp = self.create([emp_vals])
        # print("EMP", emp)
        mark_obj = self.env['student.marks']
        marks_vals = {
            'student_id': 13,
            'subject': 'Biology',
            'total_marks': 100.0,
            'obt_marks': 87.0
        }
        marks = mark_obj.create(marks_vals)
        print("MARKS", marks)

    def update_record(self):
        """
        This method will demonstrate the write method
        ---------------------------------------------
        @param self: object pointer
        """
        # Write method is used to create a record set.
        # def create(self, vals_lst):
        # @param self: object pointer
        # @param vals : A dictionary which contain fields and their respective values.
        # returns True
        emp_vals = {
            'name': 'Ajit Wadekar',
            'age': 45,
            'fee': 480.0,
            'active': True,
            'gender': 'male',
            'birthdate': fields.Date.today(),
            'first_attendance': fields.Datetime.now(),
            'standard_id': 3,
            'marks_ids': [
                # 0 = Create a record in O2M field's models
                # Syntax : [(0, 0, vals), (0, 0, vals)]
                # (0, 0, {
                #     'subject': 'English',
                #     'total_marks': 100.0,
                #     'obt_marks': 80.0
                # })
                # 1 = Update a record in O2M field's models
                # Syntax : [(1, <id>, vals), (1, id, <vals>)]
                # (1, 15,{
                #     'obt_marks': 75.0
                # })
                # Delete a record in O2M field's models
                # 2 = completely removes the record even from the o2m's table.
                # Syntax : [(2, <id>), (2, <id>)]
                # (2, 16),
                # 3 = only de-links it from the parent.
                # Syntax : [(3, <id>), (3, <id>)]
                # for e.g. here for record with id 17 it will set the many2one field to be null.
                # (3, 17)
                # 4 = links it to the record
                # Syntax : [(4, <id>), (4, <id>)]
                # (4, 17)
                # 5 = De-link all the existing records in the O2M field
                # Syntax : [(5,)] or [(5, 0)] or [(5, 0, 0)]
                # You can say it performs operation 3 with all the existing records
                # which means it does not delete the records it just de-links it from parent.
                (5,)
                # (5, 0)
                # (5, 0, 0)
            ],
            'activity_ids': [
                # Only links the new records to the parent keeping the existing records as it is.
                # (4, 5), (4, 3)
                # 6- First performs operation 5 and de-links all the existing records.
                # then performs 4 operation with all the ids given in the third element list which is a list of ids
                # Syntax : [(6, 0, list of ids)]
                (6, 0, [5, 2])
            ],
        }
        self.write(emp_vals)

    def browse_record(self):
        """
        This method demonstrates the browse method
        ------------------------------------------
        @param self: object pointer
        """
        # def browse(self, id / ids):
        # @param self: object pointer
        # @param id / ids : A single id(Integer) or list of ids
        # Returns a recordset containing the record(s) of passed id(s)
        # Browsing local records
        student = self.browse(4)
        print(student)
        students = self.browse([3, 6])
        print(students)
        # Browsing Foreign records
        std_obj = self.env['school.standard']
        standard = std_obj.browse(4)
        standards = std_obj.browse([1, 2, 3])
        print(standard)
        print(standards)
        # Using browsed recordsets to update values
        print(students.mapped('name'))
        students.write({
            'fee': 800.0
        })

    def read_record(self):
        """
        This method demonstrates read method
        ------------------------------------
        @param self: object pointer
        """
        # def read(self, fields=None, load='_classic_read')
        # @param self: object pointer
        # @param fields: List of field you want to read
        # @param load : a flag used for many2one field when you read. default value = '_classic_read'
        # it returns a list of dictionaries where the keys are the fields passed in the fields params and their values.
        # NOTE: If you do not pass any field it will read all the fields.
        # 'id' will be always there in the dictionary  even if you have not passed in the fields list.
        # Read current record
        student_dicts = self.read()
        # print("STUDENT", student_dicts)
        student_dicts = self.read(fields=['name', 'standard_id', 'marks_ids', 'activity_ids', 'ref'])
        print("STUDENT", student_dicts)
        # If load is passed anything other than _classic_read it will return only id as the value of m2o field.
        # else it will be a tuple containing id as first element and recognized / display name as the second element.
        student_dicts = self.read(fields=['name', 'standard_id', 'marks_ids', 'activity_ids', 'ref'], load='')
        print("STUDENT with Load", student_dicts)
        # Reading foreign records
        # std_obj = self.env['school.standard']
        # standard = std_obj.browse(4)
        # standard_dicts = standard.read()
        # print(standard_dicts)
        # standards = std_obj.browse([1, 2, 3])
        # standard_dicts = standards.read({'std_name', 'code'})
        # print(standard_dicts)

    def duplicate_record(self):
        """
        This method demonstartes the copy method
        -----------------------------------------
        @param self: object pointer
        """
        # Copy method is a combination of read and create methods.
        # def copy(self, default=None)
        # @param self: object pointer
        # @param default: a dictionary containing fields and values to override existing record's field before duplicating.
        # It returns the record set fo the new record.
        new_name = self.name + ' (copy)'
        # If default is passed it will override the existing field's values which is coming from existing record and then create e new record.
        dup_student = self.copy(default={'name': new_name})
        print("DUP", dup_student)

    def delete_record(self):
        """
        This method demonstrates the unlink method
        ------------------------------------------
        @param self: object pointer
        """
        # unlink() method is used to delete the records.
        # def unlink(self):
        # @param self: object pointer
        # Returns True

        # It will delete the record on which you are currently
        self.unlink()

    def search_record(self):
        """
        This method demonstrates the search and search_count method
        -----------------------------------------------------------
        @param self: object pointer
        """
        # Definition
        # @api.models
        # def search(self, args, offset=0, limit=None, order=None, count=False)
        # @param self: object pointer
        # @args : domain / list of conditions
        # @offset: no of recrods to skip
        # @limit : max no of records to fetch
        # @order : a field used to sort the searched orders
        # @count : True / False if True it will return count of records else recordset.
        # returns recordset of count based on the count param by default count=False
        # All records are given by a blank domain
        students = self.search([])
        print(students)
        # # This will give only male students
        # male_students = self.search([('gender', '=', 'male')])
        # print(male_students)
        # # Using child_of you can get all level subordinates
        # subordinate_students = self.search([('id', 'child_of', [6])])
        # print(subordinate_students)
        # # Using parent_of
        # subordinate_students = self.search([('parent_id', 'parent_of', [6])])
        # print(subordinate_students)
        # # Using only offset
        # students = self.search([], offset=3)
        # print(students)
        # # Using only limit
        # students = self.search([], limit=10)
        # print(students)
        # # Using offset and Limit
        # students = self.search([], offset=3, limit=10)
        # print(students)
        # Using Order to sort the records
        # students = self.search([], order='age')
        # print(students)
        # students = self.search([], order='age desc')
        # print(students)
        # students = self.search([], order='id,age')
        # print(students)
        # students = self.search([], order='age desc, id')
        # print(students)
        # students = self.search([], count=True)
        # print(students)
        # female_students = self.search([('gender', '=', 'female')], count=True)
        # print(female_students)

        # Search Count to return no of records based on a record
        no_of_students = self.search_count([])
        print(no_of_students)

    def search_read_record(self):
        """
        This method demonstrates the search_read method
        -----------------------------------------------
        @param self: object pointer
        """
        # search_read is a combination of search and read methods.
        # def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None)
        # @param self: object pointer
        # @param domain: domain / list of conditions
        # @param fields: a list of fields
        # @param offset: no of records to skip
        # @param limit: max no of records to fetch
        # @param order: field name to sort by
        # returns a list of dictionaries containing field as keys and values as values.

        # student_dicts = self.search_read()
        # print(student_dicts)
        # f_student_dicts = self.search_read(domain=[('gender','=','female')])
        # print(f_student_dicts)
        # f_student_dicts = self.search_read(domain=[('gender', '=', 'female')], fields=['name','standard_id'])
        # print(f_student_dicts)
        student_dicts = self.search_read(domain=[], fields=['name', 'standard_id'], offset=4, limit=5)
        print(student_dicts)
        student_dicts = self.search_read(domain=[], fields=['name', 'standard_id'], offset=4, limit=5, order='id')
        print(student_dicts)

    def read_group_record(self):
        """
        This method demonstrates the read_group method.
        -----------------------------------------------
        @param self: object pointer
        """
        # def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=None, lazy=True)
        # @param self: object pointer
        # @param domain : List of conditions
        # @param groupby : A list of fields to group by
        # @param offset : no of records to skip
        # @param limit : max no of records
        # @param lazy : True / False
        # Retuns a list of dicitonaries containing field, domain and numerical fields value based on their group operator

        # Read group method to get the values of integer and float field with group operator with the group by field and also domain if passed.
        res = self.read_group([], fields=['name', 'gender', 'age', 'fee'], groupby=['gender'])
        print(res)
        # Lazy True will just give the next group by fields in the __context parameter of the dictionary for each grouping
        res = self.read_group([], fields=['name', 'gender', 'age', 'fee'], groupby=['gender', 'standard_id'], lazy=True)
        print(res)
        # Lazy=False will give all the combination of the group by fields with the field values.
        res = self.read_group([], fields=['name', 'gender', 'age', 'fee'], groupby=['gender', 'standard_id'],
                              lazy=False)
        print(res)

    @api.model_create_multi
    def create(self, vals_lst):
        """
        Overridden create() method to set the sequence on the student
        -------------------------------------------------------------
        :param vals_lst: A list of dictionary containing fields and values
        :return: A newly created recordset.
        """
        # students = self.search([])
        # sequences = students.mapped('sequence')
        # seq = max(sequences)
        print("SELF", self)
        seq = max(self.search([]).mapped('sequence'))
        # Fetching ir.sequence Recordset from XML ID to call the next_by_id method.
        # Here the xml id is same which we have given on the record tag of sequence creation.
        sequ = self.env.ref('school_14.sequence_student')
        for vals in vals_lst:
            seq += 1
            vals.update({
                'sequence': seq,
                'annual_fees': vals.get('fee', 0.0) * 12,
                # Using Object / Blank recordset of ir.sequence fetched from environment to fetch the next sequence by code.
                # Here the code must be same as passed on the sequence creation in xml.
                # 'student_code': self.env['ir.sequence'].next_by_code('student.student'),
                'student_code': sequ.next_by_id()
            })
        # return super(Student,self).create(vals_lst)
        return super().create(vals_lst)

    def write(self, vals):
        """
        Overridden write() method to set the url
        ----------------------------------------
        :param vals: A dictionary containing fields and their respective values
        :return: True
        """
        # for student in self: # Iterate only if you're using any fields of the existing record
        # if vals.get('fee', 0.0):
        #     vals['annual_fees'] = vals['fee'] * 12
        for student in self:
            if vals.get('fee', 0.0):
                vals['annual_fees'] = vals['fee'] * 12
            else:
                vals['annual_fees'] = student.fee * 12
        # vals['annual_fees'] = vals.get('fee', 0.0) * 12
        vals['url'] = 'http://www.skyscendbs.com'
        return super().write(vals)

    @api.model
    def default_get(self, fields_list):
        """
        Overridden default_get() method to add/update default values of fields
        ----------------------------------------------------------------------
        :param self: object pointer
        :param fields: List of fields
        :return: A dictionary containing fields and their default values
        """
        print("fields", fields_list)
        res = super().default_get(fields_list)
        print("RESs",res)
        # Updating values to be defaulted to the fields
        res.update({
            'annual_fees': res.get('fee', 0.0) * 12,
            'shift': 'morning',
            # NOTE : Avoid keeping sequence on default_get
            # 'student_code': self.env['ir.sequence'].next_by_code('student.student')
        })
        print("RES", res)
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        """ fields_view_get([view_id | view_type='form'])

        Get the detailed composition of the requested view like fields, models, view architecture

        :param int view_id: id of the view or None
        :param str view_type: type of the view to return if view_id is None ('form', 'tree', ...)
        :param bool toolbar: true to include contextual actions
        :param submenu: deprecated
        :return: composition of the requested view (including inherited views and extensions)
        :rtype: dict
        :raise AttributeError:
                * if the inherited view has unknown position to work with other than 'before', 'after', 'inside', 'replace'
                * if some tag other than 'position' is found in parent view
        :raise Invalid ArchitectureError: if there is view type other than form, tree, calendar, search etc defined on the structure
        """
        # This method gets called when you click on a menu or any button where an action gets triggered.
        # All the views are loaded which are linked ot an action so you will see this method being called multiple times when an action is triggered
        # The method is called once for each type of view for e.g. tree, form and also search
        # This method calls the field_get() method and keeps a dictionary of fields which has fields and attributes which are to be displayed on field.
        print("VIEW_ID", view_id)
        print("VIEW_TYPE", view_type)
        print("TOOLBAR", toolbar)
        res = super().fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        # This method returns a dictionary which contains information about the view and the fields to be displayed on the view.
        # print("RES", res)
        return res

    @api.model
    def fields_get(self, allfields=None, attributes=None):
        """ fields_get([fields][, attributes])

        Return the definition of each field.

        The returned value is a dictionary (indexed by field name) of
        dictionaries. The _inherits'd fields are included. The string, help,
        and selection (if present) attributes are translated.

        :param allfields: list of fields to document, all if empty or not provided
        :param attributes: list of description attributes to return for each field, all if empty or not provided
        """
        # This method fetches all the fields and its attributes and gets called from fields_view_get() method
        print("ALL FIEODLS", allfields)
        print("ATTRIBUTES", attributes)
        res = super().fields_get(allfields, attributes)
        print("RES", res)
        return res

    @api.onchange('gender')
    def onchange_gender(self):
        """
        This method will change the fee based on the gender
        ---------------------------------------------------
        @param self: object pointer
        """
        # Whenever the field(s) mentioned in the decorator @api.onchange(<field>) is updated this method gets called.
        for student in self:
            if student.gender == 'male':
                student.fee = 200.0
                student.annual_fees = 200.0 * 12
            else:
                student.fee = 150.0
                student.annual_fees = 150.0 * 12

    @api.constrains('gender', 'fee')
    def check_gender_fee_limit(self):
        """
        This method checks the fee limit based on gender
        ------------------------------------------------
        @param self: object pointer
        """
        # This method gets called when you try to save the record after creation or updation.
        # This will be called when there are changes in the field mentioned in the decorator @api.constrains(<field>)
        for stud in self:
            if stud.gender == 'male' and stud.fee > 400.0:
                raise ValidationError('For Male Students the maximum fees should be 400.0!')
            elif stud.gender == 'female' and stud.fee > 300.0:
                raise ValidationError('For Female Students the maximum fees should be 300.0!')


# Model for Many2one field
class Standard(models.Model):
    _name = 'school.standard'
    _description = 'Standard'

    # Recognized name of the models
    # Displays the field on the form view in the breadcrums
    # The same field is also displayed in the relational fields like M2O and M2M
    _rec_name = 'std_name'

    std_name = fields.Char('Name')
    code = fields.Char('Code')

    def unlink(self):
        """
        Overridden unlink() method will check if there are students in the standard it will not allow to delete.
        --------------------------------------------------------------------------------------------------------
        @param self:object pointer
        :return: True
        """
        # If you want to block the deletion of records you can set an exception here.
        student_obj = self.env['student.student']
        for standard in self:
            no_of_students = student_obj.search_count([('standard_id', '=', standard.id)])
            if no_of_students:
                # UserError is an Exception class which is imported from odoo.exceptions which you can see at the top in import section.
                raise UserError('You can not delete a standard which has students!')
        return super().unlink()

    def name_get(self):
        """
        Overridden name_get() method to get the display name
        ----------------------------------------------------
        @param self: object pointer
        :return: A list of tuple containing two elements id and related string to be displayed
        """
        # This method is used to change the string which gets displayed in your relational fields like M2O and M2M
        # The same also gets displayed in the breadcrumbs which we have on the top of our form above the buttons.
        std_lst = []
        for std in self:
            std_str = ''
            if std.code:
                std_str += std.code + ' - '
            std_str += std.std_name
            std_lst.append((std.id, std_str))
        return std_lst

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """
        Overridden name_search() method to search by both code and std_name
        -----------------------------------------------------------------
        :param self: object pointer
        :param name: The string typed in the field
        :param args: The domain given on the field
        :param operator: The default operator to search the records
        :param limit: Max no of records to return
        :return: A list of tuple containing two elements id and related string to be displayed (Same as name_get)
        """
        # This method gets called whenever you type something on your relational fields M2O / M2M
        if not args:
            args = []
        args += ['|', ('std_name', operator, name), ('code', operator, name)]
        standards = self.search(args, limit=limit)
        # At the end it calls the name_get() method as it gives the same result for multiple records.
        return standards.name_get()

    @api.model
    def name_create(self, name):
        """
        Overridden name_create() method to set the code field as well.
        --------------------------------------------------------------
        :param self: object pointer
        :param name: The typed string used to create the _rec_name(recognized name field) of the models
        :return: A tuple containing id and the string. (Tuple which is given from name_get inside the list)
        """
        # This method gets called when you click on the create button from your M2O field.
        # It creates a record with the typed string and add it into your _rec_name field.
        if name:
            standard = self.create({
                'std_name': name,
                'code': name.upper()[:4],
            })
            return standard.name_get()[0]


# Model for One2many field
class Marks(models.Model):
    _name = 'student.marks'
    _description = 'Marks'

    _rec_name = 'subject'

    subject = fields.Char('Subject')
    total_marks = fields.Float('Total')
    min_marks = fields.Float('Min')
    obt_marks = fields.Float('Obtained')
    # Inverse field for One2many
    student_id = fields.Many2one('student.student', 'Student')

    # Compute Field
    percentage = fields.Float('Percentage', compute='_calc_perc')

    @api.depends('obt_marks', 'total_marks')
    def _calc_perc(self):
        """
        This method will be used to calculate the percentage
        ----------------------------------------------------
        @param self: object pointer
        """
        # self is a record set containing one or more records.
        # print("SELF", self)
        # you can access fields from recordset using . notation.
        # For e.g. <record_set>.<field_name>
        # print("SELFF TOTAL MARKS", self.total_marks)
        # You can iterate in a recordset which has multiple records.
        # with each iteration it will give you a recordset containing single record
        for mark in self:
            # print("MARK", mark)
            # print("OBT MARKS", mark.obt_marks)
            perc = 0.0
            if mark.total_marks:
                perc = mark.obt_marks * 100.0 / mark.total_marks
                if perc < 60.0:
                    perc = 0.0
            # This method must assign the value to the field from which this method is being called to compute
            mark.percentage = perc


# Model for Many2many field
class Activities(models.Model):
    _name = 'student.activity'
    _description = 'Activities'

    name = fields.Char('Name')
    code = fields.Char('Code')
    standard_id = fields.Many2one('school.standard', 'Standard')
    color = fields.Integer('Color Index')
