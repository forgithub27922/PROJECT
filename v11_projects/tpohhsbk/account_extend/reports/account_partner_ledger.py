# -*- coding: utf-8 -*-

from odoo import api, models, _


class ReportPartnerLedger(models.AbstractModel):
	_inherit = 'report.account.report_partnerledger'

	''' Partner Leder Lines show  Account code with Account Name '''
	def _lines(self, data, partner):
		result = super(ReportPartnerLedger,self)._lines(data,partner)
		for record in result:
			display_acc_code_name = str(record['a_code'] +' ' + record['a_name'])
			record['a_code'] = display_acc_code_name
		return result
