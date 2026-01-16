# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined

from odoo import api, fields, models


class HrContract(models.Model):
    """
    allows to configure different Salary structure
    """
    _inherit = 'hr.contract'
    _description = 'Employee Contract'

    grade_percentage = fields.Boolean(string="Transportation Grade",default=False)
    hra = fields.Monetary(string='Housing Allowance', tracking=True)
    transport_allowance = fields.Monetary(string="Transportation Allowance",tracking=True)
    other_allowance = fields.Monetary(string="Other Allowance", help="Other allowances")
    hr_living_allowance = fields.Monetary(string='Living Allowance', tracking=True)
    total_gross_salary = fields.Monetary(compute='_compute_total_gross_salary', store=True)

    @api.onchange('wage','grade_percentage','grade_id')
    def _onchange_grade_percentage(self):
        for contract in self:
            if contract.grade_percentage:
                contract.hra = contract.wage * contract.grade_id.hr_percentage
                contract.transport_allowance = contract.grade_id.transport_allowance
            else:
                contract.hra = 0.0
                contract.transport_allowance = 0.0

    @api.depends('wage','grade_id', 'hra', 'transport_allowance', 'hr_living_allowance', 'other_allowance')
    def _compute_total_gross_salary(self):
        for contract in self:
            # if contract.grade_percentage:
                # contract.hra = contract.wage * contract.grade_id.hr_percentage
                # contract.transport_allowance = contract.grade_id.transport_allowance
            contract.total_gross_salary = contract.wage + contract.hra \
                                          + contract.transport_allowance + contract.hr_living_allowance + contract.other_allowance
