from odoo import models, fields


class MachineAttributeWizard(models.TransientModel):
    _name = 'machine.attribute.wizard'
    _description = 'Machine Attribute Wizard'
    _rec_name = 'attribute'

    attribute = fields.Char('Attribute')
    attribute_value = fields.Char('Attribute Value')
    update_att_wiz_id = fields.Many2one('update.attribute.wizard', 'Update Attribute')


class UpdateAttributeWizard(models.TransientModel):
    _name = 'update.attribute.wizard'
    _description = 'Update Attribute Wizard'
    _rec_name = 'program_name'

    program_name = fields.Char('Program Name')
    machine_attribute_ids = fields.One2many('machine.attribute.wizard', 'update_att_wiz_id', 'Machine Attributes')

    def update_att_value(self):
        """
        This method will use to call Update Attribute method
        ----------------------------------------------------
        @param self: object pointer
        """
        machine_obj = self.env['machine.machine']
        machine = machine_obj.browse(self._context.get('active_id'))
        machine.update_attribute()


class ActivateProgramWizard(models.TransientModel):
    _name = 'activate.program.wizard'
    _description = 'Activate Program'
    _rec_name = 'program_name'

    program_name = fields.Char('Program Name')

    def activate_program(self):
        """
        This method will use to call Activate Program API
        -------------------------------------------------
        @param self: object pointer
        """
        # TODO: API to be added
        pass
