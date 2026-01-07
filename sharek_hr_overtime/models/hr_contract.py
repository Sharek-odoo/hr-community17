# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
from odoo import models, fields, api
import calendar

class HrContractOvertime(models.Model):
    _inherit = 'hr.contract'

    over_hour = fields.Monetary('Hour Wage', compute='compute_over_day_hour')
    over_day = fields.Monetary('Day Wage', compute='compute_over_day_hour')

    def get_days_of_month(self,year,month):
        return calendar._monthlen( year,  month)
        
    @api.depends('wage')
    def compute_over_day_hour(self):
        for rec in self:
            hours_per_day = rec.resource_calendar_id.hours_per_day
            rec.over_hour = rec.wage / 30 / hours_per_day
            rec.over_day = rec.wage / 30
