from odoo import api, fields, models


class res_company(models.Model):
    _inherit = "res.company"

    us_check_layout = fields.Selection( string="Check Layout", required=True,
        help="Select the format corresponding to the check paper you will be printing your checks on.\n"
             "In order to disable the printing feature, select 'None'.",
        selection=[
            ('disabled', 'None'),
            ('check_uae_print.action_print_uae_check', 'Print UAE Check'),
            ('l10n_us_check_printing.action_print_check_top', 'Check on top'),
            ('l10n_us_check_printing.action_print_check_middle', 'Check in middle'),
            ('l10n_us_check_printing.action_print_check_bottom', 'Check on bottom')
        ],
        default="check_uae_print.action_print_uae_check")