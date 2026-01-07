# -*- coding: utf-8 -*-

from odoo import models, fields, api


class hr_appraisal_goal(models.Model):
    _name = 'hr.appraisal.goal'
    _description = 'HR Appraisal Goal'
    _order = 'sequence'
    
    name = fields.Char(string='Goal Name', required=True)
    description = fields.Text(string='Description')
    sequence = fields.Integer(string='Sequence', default=10)
    weight = fields.Float(string='Weight', default=1.0)
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)