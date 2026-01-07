# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined

from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    restrict_analytic_account = fields.Boolean('Restrict Analytic Account for Accounts', related='company_id.restrict_analytic_account', readonly=False, store=True)
    account_type_ids = fields.Many2many('account.type.selection', string='Restricted Account Types',
                                        related='company_id.account_type_ids', readonly=False)