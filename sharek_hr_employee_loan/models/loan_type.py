# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined

from odoo import api, fields, models


class LoanType(models.Model):
    _name = 'loan.type'
    _rec_name = 'name'
    _description = 'Hr Loan Type'

    name = fields.Char(string="Name", required=False, )
    code = fields.Char(string="Code", required=False, )
    loan_id = fields.One2many('hr.loan', 'loan_type_id', string="Loan")
    installment = fields.Integer(string="No Of Installments", default=1, help="Number of installments")
    account_id = fields.Many2one('account.account', string="Loan Account")
    treasury_account_id = fields.Many2one('account.account', string="Treasury Account")
    journal_id = fields.Many2one('account.journal', string="Journal", domain=[('type', '=', 'general')])
    company_id = fields.Many2one('res.company', 'Company', readonly=False, help="Company",
                                 default=lambda self: self.env.user.company_id)
