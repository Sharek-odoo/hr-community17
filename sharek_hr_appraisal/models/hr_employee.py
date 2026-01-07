# -*- coding: utf-8 -*-

from odoo import models, fields, api


class hr_employee(models.Model):
    _inherit = 'hr.employee'

    competence_level_id = fields.Many2one(
        'hr.appraisal.competency.level',
        string='Competency Level',
        help='Competency level of the employee',
    )
    # appraisal_ids = fields.One2many(
    #     'hr.appraisal',
    #     'employee_id',
    #     string='Appraisals',
    #     readonly=True,
    # )
    # appraisal_count = fields.Integer(
    #     string='Appraisal Count',
    #     compute='_compute_appraisal_count',
    #     store=True,
    # )

    # @api.depends('appraisal_ids')
    # def _compute_appraisal_count(self):
    #     for employee in self:
    #         employee.appraisal_count = len(employee.appraisal_ids)