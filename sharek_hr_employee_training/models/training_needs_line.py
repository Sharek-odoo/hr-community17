from odoo import models, fields,api,_

class TrainingNeedsLine(models.Model):
    _name = 'training.needs.line'
    _description = 'Training Line'

    request_id = fields.Many2one('training.needs.request', string="Request")
    training_course_id = fields.Many2one('training.course', string="Training Course", required=True)

    name = fields.Char(string="Name")
    job_title = fields.Char(string="Job Title")
    domain_id = fields.Many2one('training.domain', string="Domain", readonly=True)
    impact_id = fields.Many2one('training.impact', string="Impact", readonly=True)
    period = fields.Selection([
        ('q1', 'First Quarter'),
        ('q2', 'Second Quarter'),
        ('q3', 'Third Quarter'),
        ('q4', 'Fourth Quarter'),
    ], string='Period', required=True)
    cost = fields.Float(string="Cost")

    @api.onchange('training_course_id')
    def _onchange_training_course_id(self):
        for rec in self:
            course = rec.training_course_id
            rec.domain_id = course.domain_id.id
            rec.impact_id = course.impact_id.id
            rec.cost = course.cost
