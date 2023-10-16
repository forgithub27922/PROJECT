from odoo import models, fields, api


class ChangeProgramname(models.TransientModel):
    _name = 'change.program.name.wiz'
    _description = 'Change Program Name Wizard'
    program_name = fields.Char('Program Name')

    def activate_program(self):
        print("\n\n\n\n YES M CALLED")
