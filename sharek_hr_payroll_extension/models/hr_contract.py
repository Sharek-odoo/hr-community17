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

    hra = fields.Monetary(string='Housing Allowance', tracking=True)
    transport_allowance = fields.Monetary(string="Transportation Allowance", tracking=True)
    other_allowance = fields.Monetary(string="Other Allowance", help="Other allowances")
    total_gross_salary = fields.Monetary(compute='_compute_total_gross_salary', store=True)

    @api.depends('wage','hra','transport_allowance', 'other_allowance')
    def _compute_total_gross_salary(self):
        for contract in self:
            contract.total_gross_salary = contract.wage + contract.hra \
                                          + contract.transport_allowance + contract.other_allowance