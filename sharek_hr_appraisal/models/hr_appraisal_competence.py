# -*- coding: utf-8 -*-

from odoo import models, fields, api


class hr_appraisal_job_competence(models.Model):
    _name = 'hr.appraisal.job.competence'
    _description = 'HR Appraisal Job Competency'
    _order = 'sequence'

    name = fields.Char(string='Competence Name', required=True)
    description = fields.Text(string='Description')
    sequence = fields.Integer(string='Sequence', default=10)
    weight = fields.Float(string='Weight', default=1.0)
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    competency_index_line_ids = fields.One2many(
        'hr.appraisal.job.competence.index',
        'competence_id',
        string='Competency Index Lines',
        copy=True,
    )
    
class hr_appraisal_competency_level(models.Model):
    _name = 'hr.appraisal.competency.level'
    _description = 'HR Appraisal Competency Level'
    _order = 'sequence'

    name = fields.Char(string='Level Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    
    
class hr_appraisal_job_competence(models.Model):
    _name = 'hr.appraisal.job.competence.index'
    _description = 'HR Appraisal Job Competency Index'
    _order = 'sequence'

    name = fields.Char(string='Index Name', required=True)
    description = fields.Text(string='Description')
    sequence = fields.Integer(string='Sequence', default=10)
    weight = fields.Float(string='Weight', default=1.0)
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    competence_level_id = fields.Many2one('hr.appraisal.competency.level', string='Competency Level')
    competence_id = fields.Many2one(
        'hr.appraisal.job.competence',
        string='Competence',
        required=True,
    )