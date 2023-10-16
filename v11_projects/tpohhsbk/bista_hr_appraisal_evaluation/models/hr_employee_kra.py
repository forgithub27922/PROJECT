from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class HrEmployeeKra(models.Model):
    _name = "hr.employee.kra"

    _order = "name desc"

    @api.depends("kra_line_ids")
    def _get_total_self_assessment(self):
        for data in self:
            for line in data.kra_line_ids:
                data.total_self_assessment += line.self_assessment

    @api.depends(
        'child_ids.kra_manager_review_ids', 'child_ids.kra_peers_review_ids')
    def _get_average_assessment(self):
        """
        count average of manager assessment and peers assessment
        :return:
        """
        for rec in self:
            if not rec.parent_id:
                mngr_review = 0.0
                for mngr_kra_rec in self.env['hr.employee.kra'].search(
                        [('assessment_type', '=', 'manager_assessment'),
                         ('parent_id', '=', rec.id)]):
                    for mngr_kra_line in mngr_kra_rec.kra_manager_review_ids:
                        mngr_review += mngr_kra_line.manager_assessment
                if rec.reviewer_ids:
                    rec.average_manager_assessment = mngr_review / len(
                        rec.reviewer_ids.ids)
                peers_review = 0.0
                for peers_kra_rec in self.env['hr.employee.kra'].search(
                        [('assessment_type', '=', 'peers_assessment'),
                         ('parent_id', '=', rec.id)]):
                    for peers_kra_line in peers_kra_rec.kra_peers_review_ids:
                        peers_review += peers_kra_line.peers_assessment
                if rec.peers_ids:
                    rec.average_peers_assessment = peers_review / len(
                        rec.peers_ids.ids)

    name = fields.Char('Name')
    employee_id = fields.Many2one("hr.employee", "Employee")
    job_id = fields.Many2one("hr.job", "Position")
    appraisal_template_id = fields.Many2one(
        'hr.appraisal.configuration', string='Appraisal Template')
    appraisal_period_id = fields.Many2one(
        'hr.appraisal.configuration.period', string='Appraisal Period')
    review_start_date = fields.Date("Start Date")
    review_end_date = fields.Date("End Date")
    kra_line_ids = fields.One2many(
        "hr.employee.kra.line", "kra_id", "Kra Line")
    kra_manager_review_ids = fields.One2many(
        "hr.kra.manager.review", "kra_id", "Kra Manager Review Lines")
    kra_peers_review_ids = fields.One2many(
        "hr.kra.peers.review", "kra_id", "Kra Line")
    strength_point = fields.Html("Strength Points")
    weakness_point = fields.Html("Weakness Points")
    reviewer_ids = fields.Many2many(
        "hr.employee", "hr_kra_employee_rel", "kra_id", "employee_id",
        "Reviewer")
    peers_ids = fields.Many2many("hr.employee", "hr_employee_kra_rel",
                                 "kra_id", "employee_id", "Peers")
    total_self_assessment = fields.Float(
        "Total Self Assessment", compute="_get_total_self_assessment",
        store=True)
    average_manager_assessment = fields.Float(
        "Average Manager Assessment",
        compute="_get_average_assessment", store=True)
    average_peers_assessment = fields.Float(
        "Average Peers Assessment", compute="_get_average_assessment",
        store=True)
    is_employee = fields.Boolean(compute="_check_is_employee")
    assessment_type = fields.Selection([
        ('self_assessment', 'Self Assessment'),
        ('manager_assessment', 'Manager Assessment'),
        ('peers_assessment', 'Peers Assessment')])
    state = fields.Selection([
        ('draft', 'Draft'), ('send_for_review', 'To be Review'),
        ('approved', 'Approved')],
        string='Status', default='draft')
    review_state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed')], string='Status', default='draft')
    parent_id = fields.Many2one('hr.employee.kra', 'KRA Reference',
                                ondelete='cascade')
    child_ids = fields.One2many('hr.employee.kra', 'parent_id',
                                string='KRA Review Reference')
    reviewed_by = fields.Many2one('hr.employee', 'Review By')
    self_review_date = fields.Date("Self Review End Date")
    mngr_pr_review_date = fields.Date("Manager/Peers Review End Date")
    confirmed_mngrs = fields.Integer(compute='calc_no_of_confirmation')
    confirmed_peers = fields.Integer(compute='calc_no_of_confirmation')
    company_id = fields.Many2one('res.company',
                                 default=lambda self: self.env.user.company_id)

    @api.multi
    def send_email_notification(self, action_id, template_id, record):
        """
        Send Email Notification
        :param action_id:
        :param template_id:
        :param record:
        :return:
        """
        display_link = False
        if action_id:
            display_link = True
        template_obj = self.env['mail.template']
        template_rec = template_obj.browse(template_id)
        base_url = self.env['ir.config_parameter'].get_param(
            'web.base.url.static')
        if template_rec:
            ctx = {
                'email_to': '',
                'base_url': base_url,
                'display_link': display_link,
                'action_id': action_id,
                'model': 'hr.employee.kra'
            }
            template_rec.with_context(ctx).send_mail(
                record.id, force_send=False)

    @api.multi
    def kra_appraisal_confirm(self):
        """
        Employee Confirm his kra and send for reviews
        :return:
        """
        self.check_state()
        data_obj = self.env['ir.model.data']
        for rec in self:
            # manage self assessment
            for kra_line_rec in rec.kra_line_ids:
                if not kra_line_rec.self_assessment or not \
                        kra_line_rec.self_remark:
                    raise ValidationError(_(
                        "Kindly, Add self assessment and remark to proceed "
                        "with your request."))
            # manage manager reviewer
            for reviewer_rec in rec.reviewer_ids:
                new_rec = rec.copy()
                new_rec.parent_id = rec.id
                new_rec.reviewed_by = reviewer_rec.id
                new_rec.assessment_type = 'manager_assessment'
                mngr_line_list = []
                for line_rec in rec.kra_line_ids:
                    mngr_line_list.append((0, 0, {
                        'question': line_rec.question,
                        'description': line_rec.description,
                        'weightage': line_rec.weightage,
                        'self_assessment': line_rec.self_assessment,
                        'measurement_ids': [
                            (6, 0, line_rec.measurement_ids.ids)]}))
                new_rec.kra_manager_review_ids = mngr_line_list
                action_id = data_obj.get_object_reference(
                    'bista_hr_appraisal_evaluation',
                    'hr_employee_kra_manager_review_action')[1] or False
                template_id = data_obj.get_object_reference(
                    'bista_hr_appraisal_evaluation',
                    'manager_review_appraisal_email_temp')[1]
                self.send_email_notification(action_id, template_id, new_rec)
            # manage peers reviewer
            for peers_rec in rec.peers_ids:
                new_rec = rec.copy()
                new_rec.parent_id = rec.id
                new_rec.reviewed_by = peers_rec.id
                new_rec.assessment_type = 'peers_assessment'
                peers_line_list = []
                for line_rec in rec.kra_line_ids:
                    peers_line_list.append((0, 0, {
                        'question': line_rec.question,
                        'description': line_rec.description,
                        'weightage': line_rec.weightage,
                        'measurement_ids': [
                            (6, 0, line_rec.measurement_ids.ids)]}))
                new_rec.kra_peers_review_ids = peers_line_list
                action_id = data_obj.get_object_reference(
                    'bista_hr_appraisal_evaluation',
                    'hr_employee_kra_peers_review_action')[1] or False
                template_id = data_obj.get_object_reference(
                    'bista_hr_appraisal_evaluation',
                    'peers_review_appraisal_email_temp')[1]
                self.send_email_notification(action_id, template_id, new_rec)
            rec.state = 'send_for_review'

    @api.multi
    def calc_no_of_confirmation(self):
        """
        Calculates no of confirmed review by manager and peers
        :return:
        """
        for rec in self:
            count_mngr = 0
            count_peers = 0
            for child_rec in rec.child_ids:
                if child_rec.assessment_type == 'manager_assessment' and \
                        child_rec.review_state == 'confirm':
                    count_mngr += 1
                if child_rec.assessment_type == 'peers_assessment' and \
                        child_rec.review_state == 'confirm':
                    count_peers += 1
            rec.confirmed_mngrs = count_mngr
            rec.confirmed_peers = count_peers

    @api.multi
    def open_reviews(self):
        """
        get related manager and peers review record
        :return:
        """
        tree_view_id = self.env.ref(
            'bista_hr_appraisal_evaluation.hr_employee_kra_tree').id
        form_view_id = self.env.ref(
            'bista_hr_appraisal_evaluation.hr_employee_kra_form').id
        assessment_type = self._context.get('assessment_type')
        if assessment_type == 'manager_assessment':
            action_name = 'KRA Manager Review'
            domain = [('assessment_type', '=', 'manager_assessment'),
                      ('parent_id', '=', self.id)]
        elif assessment_type == 'peers_assessment':
            action_name = 'KRA Peers Review'
            domain = [('assessment_type', '=', 'peers_assessment'),
                      ('parent_id', '=', self.id)]
        return {
            'name': action_name,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'view_id': tree_view_id,
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'res_model': 'hr.employee.kra',
            'domain': domain,
            'target': 'current',
        }

    @api.multi
    def reviewer_evaluation_confirm(self):
        """
        Reviewer Submit there evaluation
        :return:
        """
        for rec in self:
            rec.review_state = 'confirm'

    @api.multi
    def self_eval_reviewed(self):
        """
        review all record by hr and confirm
        :return:
        """
        self.check_state()
        for rec in self:
            for child_rec in self.child_ids:
                child_rec.review_state = 'confirm'
            rec.state = 'approved'

    def check_state(self):
        emp_kra = self.env['hr.employee.kra'].search([
            ('id', '!=', self.id), ('employee_id', '=', self.employee_id.id),
            ('appraisal_template_id', '=', self.appraisal_template_id.id),
            ('appraisal_period_id', '=', self.appraisal_period_id.id),
            ('state', 'in', ('approved', 'send_for_review'))])
        if emp_kra:
            raise ValidationError(
                'Already Found approved for same user with same period and '
                'template.')

    @api.multi
    def _check_is_employee(self):
        """
        Identifies the user with record state
        :return:
        """
        for rec in self:
            if not rec.parent_id.id:
                if not self.env.user.has_group(
                        'bista_hr_appraisal_evaluation.'
                        'group_app_evaluation_hr_user') and rec.state == \
                        'approved':
                    rec.is_employee = True
                elif self.env.user.has_group(
                        'bista_hr_appraisal_evaluation.'
                        'group_app_evaluation_hr_user'):
                    rec.is_employee = True
                else:
                    rec.is_employee = False

    @api.model
    def get_mngr_assessment_rec(self, assessment_type):
        """
        :return:
        """
        assessment_rec = self.env['hr.employee.kra'].search([
            ('assessment_type', '=', assessment_type),
            ('parent_id', '=', self.id)])
        return assessment_rec

    @api.model
    def get_peers_assessment_rec(self, assessment_type):
        """
        :return:
        """
        assessment_rec = self.env['hr.employee.kra'].search([
            ('assessment_type', '=', assessment_type),
            ('parent_id', '=', self.id)])
        return assessment_rec


class HrEmployeeKraLine(models.Model):
    _name = "hr.employee.kra.line"

    kra_id = fields.Many2one("hr.employee.kra", "KRA", ondelete='cascade')
    question = fields.Text("Question")
    description = fields.Text("Description")
    weightage = fields.Float("Weightage")
    measurement_ids = fields.Many2many(
        "appraisal.measurement", "kra_line_appraisal_rel",
        "kra_line_id", "measurement_id", "Measurement")
    self_assessment = fields.Float("Self Assessment")
    self_remark = fields.Text("Self Remark")
    assessment_type = fields.Selection([
        ('self_assessment', 'Self Assessment'),
        ('manager_assessment', 'Manager Assessment'),
        ('peers_assessment', 'Peers Assessment')],
        related='kra_id.assessment_type')

    @api.constrains('self_assessment')
    def self_assessment_validation(self):
        """
        self assessment validation
        :return:
        """
        if self.self_assessment > self.weightage:
            raise ValidationError(
                'Self assessment should not be grater then weightage.')


class HrKraManagerReview(models.Model):
    _name = "hr.kra.manager.review"

    kra_id = fields.Many2one("hr.employee.kra", "KRA", ondelete='cascade')
    question = fields.Text("Question")
    description = fields.Text("Description")
    weightage = fields.Float("Weightage")
    measurement_ids = fields.Many2many(
        "appraisal.measurement", "kra_manager_review_appraisal_rel",
        "kra_line_id", "measurement_id", "Measurement")
    self_assessment = fields.Float("Self Assessment")
    manager_assessment = fields.Float("Manager Assessment")
    manager_remark = fields.Text("Manager Remark")

    @api.constrains('manager_assessment')
    def manager_assessment_validation(self):
        """
        manager assessment validation
        :return:
        """
        if self.manager_assessment > self.weightage:
            raise ValidationError(
                'Manager assessment should not be grater then weightage.')


class HrKraPeersReview(models.Model):
    _name = "hr.kra.peers.review"

    kra_id = fields.Many2one("hr.employee.kra", "KRA", ondelete='cascade')
    question = fields.Text("Question")
    description = fields.Text("Description")
    weightage = fields.Float("Weightage")
    measurement_ids = fields.Many2many(
        "appraisal.measurement", "kra_peers_review_appraisal_rel",
        "kra_line_id", "measurement_id", "Measurement")
    peers_assessment = fields.Float("Peers Assessment")
    peers_remark = fields.Text("Peers Remark")

    @api.constrains('peers_assessment')
    def peers_assessment_validation(self):
        """
        peers assessment validation
        :return:
        """
        if self.peers_assessment > self.weightage:
            raise ValidationError(
                'peers assessment should not be grater then weightage.')
