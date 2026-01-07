from odoo import models, fields,api,_

class TrainingDomain(models.Model):
    _name = 'training.domain'
    _description = 'Training Domain'
    _rec_name = 'name'

    name = fields.Char(required=True)