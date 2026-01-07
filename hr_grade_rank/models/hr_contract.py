# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
from odoo import models, fields

class HrContract(models.Model):
    _inherit = 'hr.contract'

    grade_id = fields.Many2one("grade.grade", "Grade",related="employee_id.grade_id")
    # transport_allowance = fields.Monetary(string="Transportation Allowance", tracking=True)
