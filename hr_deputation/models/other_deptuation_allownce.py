
from odoo import models, fields, api


class HrDeputationsOtherAllownces(models.Model):
	_name = 'hr.deput.other.allownce'

	_inherit = ['mail.thread']
	
	basic_allownce_id = fields.Many2one('hr.deputations.allownce', string='Allownce')

	name = fields.Many2one('hr.deput.other.allownce.type', string='name')

	# name = fields.Char(string='Name')
	amount = fields.Float('Amount')
	percentage = fields.Integer('Percentage')

	amount_type = fields.Selection([('amount','Fixed Amont'),('percentage','Percentage')],string='Amount Type',default="amount")
	percentage_type = fields.Selection([('basic','From Basic Salary'),('allownce','From Deputation Allownce')],string='Percentage Type',default='basic')


class HrDeputationsOtherAllowncestype(models.Model):
	_name = 'hr.deput.other.allownce.type'

	name = fields.Char(string='Name')
