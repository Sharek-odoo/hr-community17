# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined

from odoo import models, fields, api


class Contract(models.Model):
    _inherit = 'hr.contract'
    _description = 'Contract Extension'

    hr_vacation_allowance = fields.Monetary(string='Vacation Allowance', tracking=True)
    hr_ticket_allowance = fields.Monetary(string='Ticket Allowance', tracking=True)
    hr_cell_phone_allowance = fields.Monetary(string='Cell Phone Allowance', tracking=True)
    hr_fuel_allowance = fields.Monetary(string='Fuel Allowance', tracking=True)
    target_allowance = fields.Monetary(string='Target Allowance', tracking=True)
    food_allowance = fields.Monetary(string='Food Allowance', tracking=True)
    fixed_overtime = fields.Monetary(string='Fixed Overtime', tracking=True)
