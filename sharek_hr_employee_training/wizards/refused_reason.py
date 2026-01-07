# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2025 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
from odoo import models, fields, api, _

class RefuseReasonWizard(models.TransientModel):
    _name = 'training.needs.request.refuse.wizard'
    _description = 'Refuse Reason Wizard'

    refuse_reason = fields.Text(string='Reason', required=True)
    training_needs_id = fields.Many2one('training.needs.request', string='Training Needs')

    def action_confirm(self):
        self.training_needs_id.write({
            'refuse_reason': self.refuse_reason,
            'state': 'refused',
        })


class TrainingRefuseReasonWizard(models.TransientModel):
    _name = 'training.request.refuse.wizard'
    _description = 'Refuse Reason Wizard'

    refuse_reason = fields.Text(string='Reason', required=True)
    training_id = fields.Many2one('hr.employee.training', string='Training Needs')

    def action_confirm(self):
        self.training_id.write({
            'refuse_reason': self.refuse_reason,
            'state': 'refused',
        })
