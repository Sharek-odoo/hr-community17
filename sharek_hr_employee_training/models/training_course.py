from odoo import models, fields,api,_

class TrainingCourse(models.Model):
    _name = 'training.course'
    _description = 'Training Course'

    name = fields.Char(string="Course Name", required=True)
    domain_id = fields.Many2one('training.domain', string="Domain", required=True)
    impact_id = fields.Many2one('training.impact', string="Impact", required=True)
    cost = fields.Float(string="Cost", required=True)