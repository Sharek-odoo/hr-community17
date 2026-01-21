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

    timeoff_days = fields.Integer('Timeoff Days',related="grade_id.timeoff_days")
    timeoff_type = fields.Many2one('hr.leave.type', domain="[('is_annual', '=', True)]")

