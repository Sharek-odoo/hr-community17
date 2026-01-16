
from odoo import models, fields, api, _
class VisaType(models.Model):
    _name = 'visa.type'
    _description = 'Visa Type Configuration'

    name = fields.Char(string="Visa Type Name", required=True)
    description = fields.Text(string="Description")

