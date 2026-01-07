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

    exit_return_journal_id = fields.Many2one("account.journal", string="Exit and Return Journal",
                                             related="company_id.exit_return_journal_id", readonly=False, store=True)
    exit_return_account_id = fields.Many2one("account.account", string="Exit and Return Account",
                                             related="company_id.exit_return_account_id", readonly=False, store=True)
    iqama_renewal_journal_id = fields.Many2one("account.journal", string="Iqama Renewal Journal",
                                               related="company_id.iqama_renewal_journal_id", readonly=False,
                                               store=True)
    iqama_renewal_account_id = fields.Many2one("account.account", string="Iqama Renewal Account",
                                               related="company_id.iqama_renewal_account_id", readonly=False,
                                               store=True)


class ResCompany(models.Model):
    """"""
    _inherit = 'res.company'

    exit_return_journal_id = fields.Many2one("account.journal", string="Exit and Return Journal")
    exit_return_account_id = fields.Many2one("account.account", string="Exit and Return Account")
    iqama_renewal_journal_id = fields.Many2one("account.journal", string="Iqama Renewal Journal")
    iqama_renewal_account_id = fields.Many2one("account.account", string="Iqama Renewal Account")
