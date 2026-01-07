
from odoo import models, fields, api


class CountryGroups(models.Model):
	_name = 'country.groups'
	_inherit = ['mail.thread']
	_rec_name = "name"

	name = fields.Char(string='Name', required=True)
	display_name = fields.Char(string='Display name', required=True)

	country_ids = fields.Many2many('res.country', string='Countries', required=True)

	@api.onchange('name')
	def onchange_name(self):
		self.display_name = self.name

