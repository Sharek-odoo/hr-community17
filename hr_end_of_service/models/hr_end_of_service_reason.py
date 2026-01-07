# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

import odoo.exceptions
from odoo.exceptions import UserError


class EndOfServiceReason(models.Model):
    _name = 'hr.end_of_service.reason'
    _description = _name
    _order = 'name'

    name = fields.Char(required=True, translate=True)
    code = fields.Char()
    reason_type = fields.Selection(
        [('termination', 'Termination'), ('resign', 'Resignation'), ('end', 'End of Contract')], required=True,default='termination')
    eos_rule_ids = fields.One2many('eos.reason.rules', 'reason_id')

    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Name must be unique!')
    ]

    def get_reward_amount(self, months, contract_id=False):
        amount = 0.0
        reward_ratio = 1
        lines = self.env['eos.reason.rules'].search([('reason_id', '=', self.id)])
        taken_months = 0.0
        if lines:
            for line in lines.filtered(lambda a: a.period_from < months):
                reward_amount = 0.0
                reward_ratio = eval(line.reward_ratio)
                period = line.period_to if months > line.period_to else months - taken_months
                if reward_ratio > 0:
                    salary = contract_id.total_gross_salary
                    reward_amount = (period / 12) * ((salary * line.percentage) / 100)
                amount += float(reward_amount)
                if reward_ratio > 0:
                    taken_months += line.period_to
        return float(amount * reward_ratio)

class EndOfServiceRules(models.Model):
    _name = 'eos.reason.rules'
    _order = 'id'

    name = fields.Char(string="Name", required=True, translate=True)
    active = fields.Boolean(default=True)
    period_from = fields.Float(string="Service Period From(Months)")
    period_to = fields.Float(string="Service Period To(Months)")
    percentage = fields.Float(string='Percentage(Calculation Factor)')
    reward_ratio = fields.Char(string='Reward Ratio')
    reason_id = fields.Many2one('hr.end_of_service.reason')
    company_id = fields.Many2one('res.company', 'Company', required=True, help="Company",
                                 index=True,
                                 default=lambda self: self.env.company)

    @api.onchange('period_from', 'period_to')
    def onchange_year(self):
        """ Function to check year configuration """
        if self.period_from and self.period_to:
            if not self.period_from < self.period_to:
                raise UserError(_("Invalid period configuration!"))
