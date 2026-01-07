# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
from odoo import models, fields, api
import calendar


class Contract(models.Model):
    _inherit = 'hr.contract'
    _description = 'Contract Extension'

    hr_productivity_allowance = fields.Monetary(string='Productivity Allowance', tracking=True)

    def get_days_of_month(self, year, month):
        return calendar._monthlen(year, month)
