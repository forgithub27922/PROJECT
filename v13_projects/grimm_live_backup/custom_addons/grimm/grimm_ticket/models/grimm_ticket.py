# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, pycompat
from datetime import datetime
TICKET_PRIORITY = [
    ('0', 'No Priority'),
    ('1', 'Low priority'),
    ('2', 'High priority'),
    ('3', 'Urgent'),
    ('4', 'Very Urgent'),
]
class GrimmTicketTag(models.Model):
    _name = 'grimm.ticket.tag'
    _description = 'Grimm Ticket Tags'

    name = fields.Char(string="Tag", required=True)


class GrimmTicketStage(models.Model):
    _name = 'grimm.ticket.stage'

    _description = 'Grimm Ticket Stages'

    _order = 'sequence, id'

    name = fields.Char(string="Stage", required=True)
    sequence = fields.Integer(string="Sequence")
    fold = fields.Boolean(string="Folded in Tasks Pipeline")

    ticket_ids = fields.One2many(comodel_name="grimm.ticket", inverse_name="stage_id", string="Tickets in stage")


class GrimmTicket(models.Model):
    _name = 'grimm.ticket'
    _description = 'Grimm Tickets'
    _inherit = [
        'mail.thread',
        'mail.activity.mixin'
    ]

    _rec_name = 'tid'

    def _get_default_stage(self):
        stage_ids = self.env['grimm.ticket.stage'].search([('sequence', '=', '1')])
        if stage_ids:
            return stage_ids[0]
        return False

    @api.model
    def _read_group_stage_ids(self, present_ids, domain, **kwargs):
        result = self.env['grimm.ticket.stage'].search([]).name_get()
        return result, None

    def change_colore_on_kanban(self):
        for record in self:
            color = "background-color: #008ae8;color: #fff;"

            today_date = datetime.strptime(str(fields.Date.today()), DEFAULT_SERVER_DATE_FORMAT)
            if record.due_date:
                due_date = datetime.strptime(str(record.due_date), DEFAULT_SERVER_DATE_FORMAT)
                delta = today_date - due_date
                if delta.days <= 0 and delta.days > -3:
                    color = "background-color: yellow;color: #0000FF;"
                elif delta.days > 0:
                    color = "background-color: #FF6347;color: #fff;"
            record.color = color

    ##############################################################################
    # Variables
    ##############################################################################

    state = fields.Selection([
        ('new', "New"),
        ('confirmed', "Confirmed"),
        ('done', "Done")
    ], default='new', track_visibility="always")

    stage_id = fields.Many2one(comodel_name="grimm.ticket.stage", string="Stage",default=_get_default_stage, group_expand='_read_group_stage_ids')
    pre_stage_id = fields.Many2one(comodel_name="grimm.ticket.stage", string="Previous Stage",default=_get_default_stage)
    tid = fields.Char(string="Ticket Number", readonly=True)
    title = fields.Char(string="Title", required=True, track_visibility="always")
    rec_link = fields.Char(string="Rercord Link")
    tags = fields.Many2many(comodel_name="grimm.ticket.tag", string="Tags", track_visibility="always")
    arranger = fields.Many2one(comodel_name="res.users", string="Arranger", track_visibility="always")
    creator = fields.Many2one(comodel_name="res.users", string="Creator", track_visibility="always",
                              default=lambda self: self.env.user)
    user_is_admin = fields.Boolean(string="User is Admin", compute="_user_is_admin", default=False)
    user_is_arranger = fields.Boolean(string="User is Arranger", compute="_user_is_arranger", default=False)
    user_is_manager = fields.Boolean(string="User is Manager", compute="_user_is_manager", default=False)
    manager = fields.Many2one(comodel_name="hr.employee", string="Manager", track_visibility="always")
    department = fields.Many2one(comodel_name="hr.department", string="Department", track_visibility="always")
    division_manager = fields.Many2one(comodel_name="res.users", string="Div Manager")
    due_date = fields.Date(string="Due Date", track_visibility="always")
    effort_estimation = fields.Float(string="Effort Estimation", track_visibility="always")
    description = fields.Text(string="Description", track_visibility="always")
    is_my_department = fields.Boolean(compute='computed_is_my_department', search='search_by_department')
    color = fields.Char('Color Index', compute="change_colore_on_kanban")
    priority = fields.Selection(TICKET_PRIORITY, string='Priority', default='0')

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        # retrieve job_id from the context and write the domain: ids + contextual columns (job or default)
        ticket_id = self._context.get('default_ticket_id')
        search_domain = [('ticket_ids', '=', False)]
        if ticket_id:
            search_domain = ['|', ('ticket_ids', '=', job_id)] + search_domain
        if stages:
            search_domain = ['|', ('id', 'in', stages.ids)] + search_domain

        stage_ids = stages._search(search_domain, order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)

    def computed_is_my_department(self):
        for ticket in self:
            if not ticket.department:
                ticket.is_my_department = True
            else:
                user_ids = [member.user_id.id for member in ticket.department.member_ids]
                if self.env.user and self.env.user.id in user_ids:
                    ticket.is_my_department = True
                else:
                    ticket.is_my_department = False

    def search_by_department(self, operator, value):
        if self.env.user:
            members = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)])
            department_ids = [member.department_id.id for member in members]
            department_ids = set(department_ids)
            if department_ids:
                return [('department', 'in', list(department_ids))]
        return [('id', '!=', None)]

    _group_by_full = {
        'stage_id': _read_group_stage_ids
    }

    ##############################################################################
    # Model overrides
    ##############################################################################

    @api.model
    def create(self, vals):
        vals['tid'] = self.env['ir.sequence'].next_by_code('grimm.ticket.sequence')
        res = super(GrimmTicket, self).create(vals)
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        database_name = self._cr.dbname
        res.rec_link = '%s/web?db=%s#id=%s&view_type=form&model=grimm.ticket' % (
            base_url, database_name, self.id)
        return res

    def write(self, vals):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        database_name = self._cr.dbname
        vals['rec_link']='%s/web?db=%s#id=%s&view_type=form&model=grimm.ticket' % (
        base_url, database_name, self.id)

        if 'department' in vals:
            _department = self.env['hr.department'].browse(vals['department'])
            if _department.manager_id:
                vals['manager'] = _department.manager_id.id
            else:
                vals['manager'] = None
        # if 'stage_id' in vals: # Colleagues don't want email when state is changed.
        #
        #     stage_ids = self.env['grimm.ticket.stage'].search([('sequence', '=', '1')])
        #     if self.stage_id:
        #         query = "update grimm_ticket set pre_stage_id=%s,stage_id=%s where id=%s"%(self.stage_id.id,vals['stage_id'],self.id)
        #     else:
        #         query = "update grimm_ticket set pre_stage_id=%s,stage_id=%s where id=%s" % (vals['stage_id'], vals['stage_id'], self.id)
        #     self._cr.execute(query)
        #     self._cr.commit()
        #     if vals['stage_id'] == stage_ids[0].id:
        #         self.arranger = None
        #     else:
        #         # TODO: Check all situations
        #         # 1. what if arranger is set? change? error? -> manager action?
        #         if not self.arranger:
        #             self.arranger = self.env.uid
        #     template = self.env.ref('grimm_ticket.ticket_stage_email_template', raise_if_not_found=False)
        #     email_list = ""
        #     for follower in self.message_follower_ids:
        #         email_list = email_list + str(follower.partner_id.email) + ","
        #     if self.manager:
        #         email_list = email_list + str(self.manager.user_id.login) + ","
        #     template.email_to = str(email_list)[:-1]
        #     if template:
        #         template.sudo().send_mail(self.id, force_send=True)
        res = super(GrimmTicket, self).write(vals)
        return res

    ##############################################################################
    # checks for user role
    ##############################################################################

    def _user_is_admin(self):
        if self.env.uid == SUPERUSER_ID:
            self.user_is_admin = True
        else:
            self.user_is_admin = False

    def _user_is_arranger(self):
        if self.arranger and self.arranger.id == self.env.uid:
            self.user_is_arranger = True
        else:
            self.user_is_arranger = False

    ##############################################################################
    # Actions for states
    ##############################################################################

    def action_new(self):
        if self.arranger:
            if self.arranger == self.env['res.users'].browse(self.env.uid):
                self.arranger = None
                stage_ids = self.env['grimm.ticket.stage'].search([('sequence', '=', '1')])
                self.stage_id = stage_ids[0].id

    def action_confirm(self):
        if not self.arranger:
            self.arranger = self.env.uid  # self.env['res.users'].browse(self.env.uid).partner_id

        self.state = 'confirmed'

    def action_done(self):
        self.state = 'done'

    ##############################################################################
    # OnChange
    ##############################################################################

    @api.onchange('arranger')
    def _onchange_arranger(self):
        stage_ids = self.env['grimm.ticket.stage'].search([('sequence', '=', '1')])
        if self.arranger and self.stage_id == stage_ids[0].id:
            self.action_confirm()
        else:
            self.action_new()
