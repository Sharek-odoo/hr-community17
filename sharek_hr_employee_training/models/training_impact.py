from odoo import models, fields,api,_

class TrainingImpact(models.Model):
    _name = 'training.impact'
    _description = 'Training Impact'
    _rec_name = 'name'

    name = fields.Char(required=True)