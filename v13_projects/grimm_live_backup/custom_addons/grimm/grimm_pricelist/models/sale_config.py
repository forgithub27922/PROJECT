# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    price_rising_alarm_percent = fields.Float(string="Price Rising Alarm", help="Maximum Price Rising in Percent",
                                              default=10)
    price_cutting_alarm_percent = fields.Float(string="Price Cutting Alarm", help="Maximum Price Cutting in Percent",
                                               deafult=10)
    price_alarm_emails = fields.Text(string='Alarm E-Mail-Addresses', default='')
    cost_price_list_id = fields.Many2one(comodel_name='product.pricelist', string='Operating Cost Price List')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        price_rising_alarm_percent = float(ICPSudo.get_param("price.rising.alarm.percent", default=10))
        price_cutting_alarm_percent = float(ICPSudo.get_param("price.cutting.alarm.percent", default=10))
        price_alarm_emails = ICPSudo.get_param("price.alarm.emails", default='')
        cost_price_list_id = int(ICPSudo.get_param("cost.price.list", default=False))
        res.update(price_rising_alarm_percent=price_rising_alarm_percent,
                   price_cutting_alarm_percent=price_cutting_alarm_percent,
                   price_alarm_emails=price_alarm_emails,
                   cost_price_list_id=int(cost_price_list_id) if cost_price_list_id else False)
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param("price.rising.alarm.percent", self.price_rising_alarm_percent or '')
        ICPSudo.set_param("price.cutting.alarm.percent", self.price_cutting_alarm_percent or '')
        ICPSudo.set_param("price.alarm.emails", self.price_alarm_emails or '')
        ICPSudo.set_param("cost.price.list", self.cost_price_list_id.id if self.cost_price_list_id else False)
