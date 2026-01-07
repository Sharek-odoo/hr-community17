from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    education_child_account_id = fields.Many2one(
        'account.account', 
        string="Education Allowance Account",
        config_parameter='sharek_financial_requests.education_child_account_id'
    )

    advance_salary_account_id = fields.Many2one(
        'account.account', 
        string="Advance Salary Account",
        config_parameter='sharek_financial_requests.advance_salary_account_id'
    )

    financial_claim_account_id = fields.Many2one(
        'account.account', 
        string="Financial Claim Account",
        config_parameter='sharek_financial_requests.financial_claim_account_id'
    )

    overtime_request_account_id = fields.Many2one(
        'account.account', 
        string="Overtime Account",
        config_parameter='sharek_financial_requests.overtime_request_account_id'
    )

    perpetual_custody_account_id = fields.Many2one(
        'account.account', 
        string="Perpetual Custody Account",
        config_parameter='sharek_financial_requests.perpetual_custody_account_id'
    )

    temporary_custody_account_id = fields.Many2one(
        'account.account', 
        string="Temporary Custody Account",
        config_parameter='sharek_financial_requests.temporary_custody_account_id'
    )

    financial_request_journal_id = fields.Many2one(
        'account.journal', 
        string="Financial Requests Journal",
        domain="[('type', '=', 'purchase')]",
        config_parameter='sharek_financial_requests.financial_request_journal_id'
    )