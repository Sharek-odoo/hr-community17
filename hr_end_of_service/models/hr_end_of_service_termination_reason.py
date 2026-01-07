# -*- coding: utf-8 -*-

from odoo import models, fields

class EndOfServiceTerminationReason(models.Model):
    _name = 'hr.end_of_service.termination_reason'
    _description = _name
    _order = 'name'
    
    name = fields.Char(required=True, translate = True)
    code = fields.Char()
    
    _sql_constraints= [
            ('name_unqiue', 'unique(name)', 'Name must be unique!')
        ]    
    