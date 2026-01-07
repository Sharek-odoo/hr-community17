# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
from odoo import models, fields


class HolidaysType(models.Model):
    _inherit = "hr.leave.type"

    calc_type = fields.Selection([('work', 'Working Days'), ('calendar', 'Calendar Days')], string='Calculation Type',
                                 required=True, default='work')
    for_specific_gender = fields.Boolean('For Specific Gender')
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')], string='Type')
    is_annual = fields.Boolean('Annual Leave')
    allow_negative = fields.Boolean('Allow Negative')
    negative_limit = fields.Integer('Limit')
    required_delegation = fields.Boolean(string='Required Delegation')
    required_ticket = fields.Boolean(string='Required Ticket')
    religion_ids = fields.Many2many('religion.religion', string='Religions')
    trial_period = fields.Boolean(string='Allowed in trial period')
