from odoo import models, fields,api,_

class TrainingAcademy(models.Model):
    _name = 'training.academy'
    _description = 'Training Impact'
    _rec_name = 'name'

    name = fields.Char(required=True)