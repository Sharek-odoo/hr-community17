# -*- coding: utf-8 -*-

from odoo import models, fields,api

class HrContractInherit(models.Model):
    _inherit = 'hr.contract'

    in_trial_period = fields.Boolean(string="In Trial Period")
    evaluation_ids = fields.One2many('hr.probation.evaluation', 'contract_id', string="Probation Evaluations")
    

    @api.depends('employee_id')
    def _compute_evaluation_id(self):
        for contract in self:
            contract.evaluation_id = self.env['hr.probation.evaluation'].search([
                ('employee_id', '=', contract.employee_id.id)
            ], limit=1)
