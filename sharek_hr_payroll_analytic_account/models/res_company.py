# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
from odoo import models, fields, api

class ResCompany(models.Model):
    _inherit = "res.company"
    
    restrict_analytic_account = fields.Boolean('Restrict Analytic Account for Accounts')
    account_type_ids = fields.Many2many('account.type.selection', string='Restricted Account Types')