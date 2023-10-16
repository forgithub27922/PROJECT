# -*- coding: utf-8 -*-


from odoo import models, fields, api, _


class AssetLocation(models.Model):
    _name = 'grimm.asset.location'
    _description = 'Grimm Asset Locations'

    name = fields.Many2one('asset.location.value', string="Value")
    placement = fields.Char(string="Placement")
    asset_id = fields.Many2one("grimm.asset.asset", string="Asset", ondelete="cascade", index=True)


class AssetLocationValue(models.Model):
    _name = 'asset.location.value'
    _description = 'Asset location value'

    name = fields.Char(string="Value")
    asset_location_id = fields.One2many("grimm.asset.location", "name", string="Asset Location")


class AssetType(models.Model):
    _name = 'grimm.asset_type'
    _description = 'Grimm asset type'

    name = fields.Char(string="Type")


class AssetDocument(models.Model):
    _name = 'asset.document'
    _description = 'Asset documents'

    asset_id = fields.Many2one('grimm.asset.asset', string='Gerät', ondelete='cascade')
    name = fields.Char(string='Name')
    filename = fields.Char(string='Datei Name')
    attachment = fields.Binary('Datei', attachment=True)

    @api.onchange('filename')
    def onchange_filename(self):
        self.name = self.filename


class AssetAsset(models.Model):
    _name = 'grimm.asset.asset'
    _inherit = ['mail.thread']
    _description = 'Asset'

    @api.depends('product_id')
    def _get_matchcode(self):
        self.ensure_one()
        if self.product_id:
            if not self.code_seq:
                self.code_seq = self.env['ir.sequence'].get('grimm.asset.seq')
            self.matchcode = str(self.product_id.default_code) + '-' + str(self.code_seq)

    def _get_history_count(self):
        for record in self:
            record.previous_owners_count = self.env['grimm.owner.history'].sudo().search_count(
                [('record_id', '=', record.id), ('active', '=', False), ('model_name', '=', 'grimm.asset.asset')])

    def _get_service_parts(self):
        for record in self:
            record.service_part_ids = record.product_id.service_part_ids

    def _get_accessory_parts(self):
        for record in self:
            record.accessory_part_ids = record.product_id.accessory_part_ids

    def _concat_location(self):
        for record in self:
            record.location_concat = (record.building.name or '') + ' ' + \
                                     (record.floor.name or '') + ' ' + (record.room.name or '')

    def _get_maintenance_state(self):
        for record in self:
            sale_order_count = self.env['sale.order'].sudo().search_count(
                [('asset_ids', 'in', record.id)])
            if sale_order_count > 0:
                record.has_maintenance = True
            else:
                record.has_maintenance = False

    name = fields.Char(string='Name', required=True)
    serial_number = fields.Char(string='Serial Number', track_visibility='onchange')
    manufacture_date = fields.Date(string='Manufacture Date', track_visibility='onchange')
    placing_date = fields.Date(string='Placing Date', track_visibility='onchange')
    description = fields.Text(string='Technical Features', track_visibility='onchange')
    attachment_ids = fields.One2many(
        'asset.document', 'asset_id', string='Attachments', track_visibility='onchange')
    location_ids = fields.One2many('grimm.asset.location', 'asset_id', string="Location", copy=True)
    location_description = fields.Text(string='Location Description', track_visibility='onchange')
    customer_inventory_no = fields.Char(string='Customer Inventory No', track_visibility='onchange')
    tags = fields.Many2many('grimm.asset.tag', string='Tags', track_visibility='onchange')
    tagnames = fields.Char('grimm.asset.tag', related="tags.name")
    active = fields.Boolean("Active", default=True, track_visibility='onchange')
    asset_facility_id = fields.Many2one('grimm.asset.facility', string='Asset Facility')
    survey_id = fields.Many2one('survey.survey', string='Work Survey', track_visibility='onchange')
    product_id = fields.Many2one('product.template', string='Typ/Model', domain=[
        ('is_spare_part', '=', False), ('is_tool', '=', False)], track_visibility='onchange')
    product_attachment_ids = fields.One2many(
        string='Product Attachments', related='product_id.product_attachment_ids')
    code_seq = fields.Char(string="Sequence")
    matchcode = fields.Char(string='Match code', default=lambda self: _('New'))
    brand = fields.Char(related='product_id.product_brand_id.name',
                        string='Brand')
    product_price = fields.Float(related='product_id.lst_price', string='Sales Price')
    internal_cat = fields.Char(related='product_id.categ_id.name', string='Internal Category')
    default_code = fields.Char(related='product_id.default_code', string='Article Number')
    product_img = fields.Image(related='product_id.image_1920', track_visibility='onchange')
    has_maintenance = fields.Boolean('Maintenance', compute='_get_maintenance_state')
    previous_owners_count = fields.Integer(string='Ex Owners', compute='_get_history_count')
    connection_ids = fields.One2many(
        'product.connection', 'asset_id', string='Connections')
    service_part_ids = fields.One2many(
        string='Service Parts', related='product_id.service_part_ids')
    accessory_part_ids = fields.One2many(
        string='Accessory Parts', related='product_id.accessory_part_ids')
    spare_part_ids = fields.Many2many(string='Spare Parts', related='product_id.spare_part_ids')
    tool_ids = fields.Many2many(string='Tools', related='product_id.tool_ids')
    condition = fields.Selection([
        ('1star', '1 Star'),
        ('2star', '2 Star'),
        ('3star', '3 Star'),
        ('4star', '4 Star'),
        ('5star', '5 Star'),
    ], string='Condition', required=True, default='1star',
        help="Describes the condition of an asset.")

    partner_owner = fields.Many2one('res.partner', string='Owner', track_visibility='onchange')
    partner_owner_street = fields.Char(
        'res.partner', related='partner_owner.street')
    partner_owner_city = fields.Char('res.partner', related='partner_owner.city')
    partner_owner_zip = fields.Char('res.partner', related='partner_owner.zip')
    partner_owner_ref = fields.Char('res.partner', related='partner_owner.ref')
    partner_contact = fields.Many2one('res.partner', string='Contact', track_visibility='onchange')
    partner_invoice = fields.Many2one('res.partner', string='Invoice', track_visibility='onchange')
    partner_delivery = fields.Many2one(
        'res.partner', string='Delivery', track_visibility='onchange')
    beneficiary = fields.Many2one('res.partner', 'Beneficiary', track_visibility='onchange')

    @api.model
    def create(self, vals):
        if vals.get('matchcode', _('New')) == _('New'):
            vals['matchcode'] = self.env['ir.sequence'].next_by_code('grimm.asset.seq') or _('New')
        result = super(AssetAsset, self).create(vals)
        if result.asset_facility_id:
            result.update_contact_addresses(
                result.get_contacts_dict_from_facility(result.asset_facility_id.id), False)
        return result

    def write(self, vals):
        if vals.get('matchcode', _('/')) == _('/'):
            vals['matchcode'] = self.env['ir.sequence'].next_by_code('grimm.asset.seq') or _('New')
        for record in self:
            if 'asset_facility_id' in vals and vals['asset_facility_id']:
                vals.update(record.get_contacts_dict_from_facility(vals['asset_facility_id']))
        result = super(AssetAsset, self).write(vals)
        return result

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.spare_part_ids = self.product_id.spare_part_ids
            self.tool_ids = self.product_id.tool_ids
            self.accessory_part_ids = self.product_id.accessory_part_ids
            self.service_part_ids = self.product_id.service_part_ids
            self.brand = self.product_id.product_brand_id.name
            self.description = self.product_id.description_sale
            self.name = self.product_id.name
            values = []
            for val in self.product_id.connection_ids:
                line_item = {
                    'connection_unit': val.connection_unit.id,
                    'connection_medium': val.connection_medium.id,
                    'connection_spec': val.connection_spec,
                    'connection_value': val.connection_value
                }
                #values += [line_item]
                self.connection_ids = [(0, 0, line_item)]
            #self.connection_ids = values

    def action_partner_history(self):
        self.ensure_one()
        return self.env['grimm.owner.history'].get_owner_history_action('grimm.asset.asset', self.id)

    # This is could be removed when there is no more partners without history links
    @api.model
    def _check_active_partners(self):
        assets = self.env['grimm.asset.asset'].search(
            [('partner_owner', '!=', None), ('active', '=', True)])
        for asset in assets:
            owner_link = self.env['grimm.owner.history'].search(
                [('partner_id', '=', asset.partner_owner.id), ('model_name', '=', 'grimm.asset.asset'),
                 ('active', '=', True)])
            if not owner_link:
                self.env['grimm.owner.history'].change_owner(
                    'grimm.asset.asset', asset, asset.partner_id)

    def get_contacts_dict_from_facility(self, facility_id):
        self.ensure_one()
        facility = self.env['grimm.asset.facility'].browse([facility_id])
        res = {}
        if facility:
            res = {
                'partner_owner': facility.partner_owner.id,
                'partner_contact': facility.partner_contact.id,
                'partner_invoice': facility.partner_invoice.id,
                'partner_delivery': facility.partner_delivery.id,
            }
        return res

    @api.onchange('asset_facility_id')
    def onchange_asset_facility_id(self):
        if self.asset_facility_id:
            if not self.partner_owner:
                self.partner_owner = self.asset_facility_id.partner_owner.id
                self.partner_contact = self.asset_facility_id.partner_contact.id
                self.partner_invoice = self.asset_facility_id.partner_invoice.id
                self.partner_delivery = self.asset_facility_id.partner_delivery.id

    def update_contact_addresses(self, vals, propagate):
        self.write(vals)
        for record in self:
            current_owner = self.env['grimm.owner.history'].get_current_owner(
                'grimm.asset.asset', record.id)
            if record.partner_owner != current_owner:
                self.env['grimm.owner.history'].change_owner(
                    'grimm.asset.asset', record, record.partner_owner)


class AssetTag(models.Model):
    _name = 'grimm.asset.tag'
    _description = 'Asset Tag'

    name = fields.Char(string='Name')
    color = fields.Integer('Color Index')
