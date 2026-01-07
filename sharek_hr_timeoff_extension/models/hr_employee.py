# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined

from odoo import fields, models, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    religion_id = fields.Many2one('religion.religion', string='Religion')
