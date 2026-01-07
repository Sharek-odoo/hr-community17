# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
from odoo import fields, models


class ConfigSettings(models.TransientModel):
    """"""
    _inherit = 'res.config.settings'

    product_id = fields.Many2one("product.product", string="Insurance Product", related="company_id.product_id",
                                 readonly=False, store=True)
    analytic_account_id = fields.Many2one("account.analytic.account", string="Analytic Account",
                                          related="company_id.analytic_account_id", readonly=False, store=True)
    journal_id = fields.Many2one("account.journal", string="Insurance Journal",
                                 related="company_id.journal_id", readonly=False, store=True)
    period_before_notification = fields.Integer(string="Period Before Notification",
                                                related="company_id.period_before_notification", readonly=False,
                                                store=True)


class ResCompany(models.Model):
    """"""
    _inherit = 'res.company'

    product_id = fields.Many2one("product.product", string="Product")
    analytic_account_id = fields.Many2one("account.analytic.account", string="Analytic Account")
    journal_id = fields.Many2one("account.journal", string="Insurance Journal")
    period_before_notification = fields.Integer(string="Period Before Notification", default=30)
