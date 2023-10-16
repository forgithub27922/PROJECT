from odoo import models, fields, api
from odoo.exceptions import UserError


class FleetLocation(models.Model):
    _name = 'fleet.location'

    name = fields.Char('Name')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)
    driver_ids = fields.One2many('res.partner', 'location_id', 'Drivers/Custodians')
    no_of_drivers = fields.Integer(compute='_count_drivers', string='#Drivers')
    vehicle_ids = fields.One2many('fleet.vehicle', 'location_id', 'Vehicles')
    no_of_vehicles = fields.Integer(compute='_count_vehicles', string='#Vehicles')
    color = fields.Integer('Color Index')

    @api.multi
    def _count_drivers(self):
        driver_obj = self.env['res.partner']
        for loc in self:
            loc.no_of_drivers = driver_obj.search([('driver', '=', True), ('location_id', '=', loc.id)], count=True)

    @api.multi
    def _count_vehicles(self):
        vehicle_obj = self.env['fleet.vehicle']
        for loc in self:
            loc.no_of_vehicles = vehicle_obj.search([('location_id', '=', loc.id)], count=True)


class FleetImage(models.Model):
    _name = 'fleet.image'
    _description = 'Fleet Images'

    image_file = fields.Binary('Image')
    fleet_id = fields.Many2one('fleet.vehicle', 'Vehicle')


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    location_id = fields.Many2one('fleet.location', 'Current Location')
    brand_id = fields.Many2one('fleet.vehicle.model.brand', 'Brand')
    photo = fields.Binary('Photo')
    image_ids = fields.One2many('fleet.image', 'fleet_id', 'Images')

    @api.onchange('model_id')
    def onchange_model(self):
        if self.model_id:
            self.brand_id = self.model_id.brand_id.id
        else:
            self.brand_id = False

    _sql_constraints = [
        ('chasis_no_unique', 'unique(vin_sn)', 'The Chassis No must be unique for each car!'),
        ('license_plate_unique', 'unique(license_plate)', 'The License Plate must be unique for each car!')
    ]


class FleetTransaction(models.Model):
    _inherit = 'mail.thread'
    _name = 'fleet.transaction'

    _description = 'Fleet Transactions'
    _order = 'date'

    name = fields.Char('Name')
    date = fields.Date('Date', track_visibility='onchange', default=fields.Date.context_today, index=True)
    vehicle_id = fields.Many2one('fleet.vehicle', 'Vehicle', index=True)
    from_loc_id = fields.Many2one('fleet.location', 'From Location', track_visibility='onchange')
    to_loc_id = fields.Many2one('fleet.location', 'To Location', track_visibility='onchange')
    from_partner_id = fields.Many2one('res.partner', 'From Driver/Custodian', track_visibility='onchange')
    to_partner_id = fields.Many2one('res.partner', 'To Driver/Custodian', track_visibility='onchange')
    amount = fields.Float('Amount')
    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', 'Confirmed'),
                              ('cancel', 'Cancelled'),
                              ('mngr_approval', 'Approved by Manager'),
                              ('pm_approval', 'Approved by Palace Manager'),
                              ('done', 'Done')],
                             'State', track_visibility='onchange', default='draft', index=True, copy=False)
    type = fields.Selection([('location', 'Location Transfer'),
                             ('personal', 'Driver/Custodian Transfer'),
                             ('scrap', 'Scrap'),
                             ('sell', 'Sell'),
                             ('gift', 'Gift')], 'Type', track_visibility='onchange', index=True)
    notes = fields.Text('Notes')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)

    @api.model
    def create(self, vals):
        """
        Overridden create method to add the sequence to the transactions
        ----------------------------------------------------------------
        @param self: object pointer
        @param vals: Dictionary containing fields and values to create a record.
        """
        # Generate the new sequence for the fleet transaction
        seq = self.env['ir.sequence'].next_by_code('fleet.transaction') or ('New')
        # Get the Location and Partner from Vehicle
        vehicle = self.env['fleet.vehicle'].browse(vals.get('vehicle_id'))
        vals.update({
            'name': seq,
            'from_loc_id': vehicle.location_id.id,
            'from_partner_id': vehicle.driver_id.id
        })
        return super(FleetTransaction, self).create(vals)

    @api.multi
    def unlink(self):
        """
        Overridden unlink method to check the state of the transaction before deletion.
        --------------------------------------------------------------------------------        @param self:object pointer
        """
        for txn in self:
            if txn.state != 'draft':
                raise UserError('You can only delete draft transactions!')
        return super(FleetTransaction, self).unlink()

    @api.onchange('vehicle_id')
    def onchange_vehicle(self):
        """
        This method is used to set the Current Location and Current Custodian/Driver on the Transaction.
        ------------------------------------------------------------------------------------------------
        @param self: object pointer
        """
        for txn in self:
            if txn.type == 'personal':
                txn.to_loc_id = self.vehicle_id.location_id and self.vehicle_id.location_id.id
            if self.vehicle_id:
                self.from_loc_id = self.vehicle_id.location_id and self.vehicle_id.location_id.id
                self.from_partner_id = self.vehicle_id.driver_id and self.vehicle_id.driver_id.id
            else:
                self.from_loc_id = False
                self.from_partner_id = False

    @api.multi
    def confirm_txn(self):
        """
        This method is used to confirm the Transaction.
        -----------------------------------------------
        @param self: object pointer
        """
        for txn in self:
            # Check the  conditions to make sure of the control of transactions
            if txn.type == 'location':
                if txn.from_loc_id and (txn.from_loc_id == txn.to_loc_id):
                    raise UserError('For location transfer you can not have destination location same as \
                                     source location!')
            elif txn.type == 'personal':
                if not txn.vehicle_id.location_id:
                    raise UserError('The vehicle must be allocated to a location \
                                     before you allocate to a driver/custodian!')
                if txn.from_partner_id and (txn.from_partner_id == txn.to_partner_id):
                    raise UserError('For driver/custodian transfer you can not have the same driver \
                                     as assignee and releaser!')
            txn.state = 'confirm'

    @api.multi
    def cancel_txn(self):
        """
        This method is used to cancel the Transaction.
        It also rollbacks the assignation of the Location and Custodian as well.
        ------------------------------------------------------------------------
        @param self: object pointer
        """
        for txn in self:
            # Reset the Location or Driver as per the Transaction Type
            if txn.type == 'location':
                txn.vehicle_id.location_id = txn.from_loc_id.id
            elif txn.type == 'personal':
                txn.vehicle_id.driver_id = txn.from_partner_id.id
            else:
                txn.vehicle_id.location_id = txn.from_loc_id.id
                txn.vehicle_id.driver_id = txn.from_partner_id.id
            # Unarchive the vehicle if sold, scrapped or gifted.
            if txn.type in ('sell', 'scrap', 'gift'):
                txn.vehicle_id.active = True
            txn.state = 'cancel'

    @api.multi
    def mngr_approve_txn(self):
        """
        This method is used to approve the Transaction by the Manager.
        This will be used only in case of Scrap, Gift or Selling the Vehicle.
        ---------------------------------------------------------------------
        @param self: object pointer
        """
        self.state = 'mngr_approval'

    @api.multi
    def pm_approve_txn(self):
        """
        This method is used to approve the Transaction by the Palace Manager.
        This will be used only in case of Scrap, Gift or Selling the Vehicle.
        ---------------------------------------------------------------------
        @param self: object pointer
        """
        self.state = 'pm_approval'

    @api.multi
    def complete_txn(self):
        """
        This method is used to complete the Transaction.
        It will also set the Current Location and Custodian/Driver on the Vehicle.
        --------------------------------------------------------------------------
        @param self: object pointer
        """
        for txn in self:
            if txn.type == 'location':
                txn.vehicle_id.write({
                    'location_id': txn.to_loc_id and txn.to_loc_id.id or False,
                    'driver_id': False
                })
            elif txn.type == 'personal':
                txn.vehicle_id.write({
                    'driver_id': txn.to_partner_id and txn.to_partner_id.id or False
                })
            else:
                txn.vehicle_id.write({
                    'location_id': txn.to_loc_id and txn.to_loc_id.id or False,
                    'driver_id': txn.to_partner_id and txn.to_partner_id.id or False
                })

            # Archive the vehicle if sold, scrapped or gifted.
            if txn.type in ('sell', 'scrap', 'gift'):
                txn.vehicle_id.active = False
            txn.state = 'done'

    @api.multi
    def set_to_draft_txn(self):
        """
        This method is used to set the cancelled transaction to draft.
        --------------------------------------------------------------
        @param self: object pointer
        """
        for txn in self:
            # Set the state as draft
            txn.state = 'draft'


class ResPartner(models.Model):
    _inherit = 'res.partner'

    location_id = fields.Many2one('fleet.location', 'Location')