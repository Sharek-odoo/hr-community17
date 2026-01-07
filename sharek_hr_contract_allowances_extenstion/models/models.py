# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined

from odoo import models, fields, api

class Allowances_Type(models.Model):
	_name = 'allowance.type'

	name = fields.Char('Allownce Name',required=True)
	code = fields.Char('Allownce Code',required=True)
class HRAllowances(models.Model):
	_name = "hr.allowances"

	contract_id = fields.Many2one('hr.contract')
	allowance_id = fields.Many2one('allowance.type',string='Allownce Name')
	code = fields.Char('Allownce Code',related='allowance_id.code')
	allowance_value = fields.Float('Allowance Value')
class sharek_hr_contract_allowances(models.Model):
    _inherit = 'hr.contract'

    allowances = fields.One2many('hr.allowances','contract_id',string="Contract")

    def get_allowances_by_code(self,code):
    	all_allowances = self.allowances.search([('code','=',code)])
    	total = sum([line.allowance_value for line in all_allowances])
    	return total
   

