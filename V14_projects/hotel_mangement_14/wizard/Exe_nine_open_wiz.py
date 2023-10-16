from odoo import fields, models


class ExeNineOpenWiz(models.TransientModel):
    _name = 'exe.nine.open.wiz'
    _desc = 'Exercise Nine Open Wizard'

    charges_ids = fields.Many2many('customer.charges', string='Customer Charges')

    def action_charges_id(self):

        print("\n\nOpen wizard call---->>>>>")
        customer_id = self._context.get('active_id')
        action = self.env.ref('hotel_mangement_14.action_charges').read()[0]
        print("\n\naction", action)
        if len(self.charges_ids) <= 1:
            print("\n\nless data")
            form_view = self.env.ref('hotel_mangement_14.view_charges_form')
            print("\n\nform_view", form_view)
            action.update({
                'res_id': customer_id,
                'views': [(form_view.id, 'form')],
                'view_mode': 'form',
                'domain': [('customer_id', '=', customer_id)]
            })
            print("----->",action)
        else:
            print("\n\nmore data")
            tree_view = self.env.ref('hotel_mangement_14.view_charges_tree')
            print("\n\ntree_view", tree_view)
            action.update({
                'views': [(tree_view.id, 'tree')],
                'view_mode': 'tree',
                'domain': [('customer_id', '=', customer_id)]
            })

        return action
