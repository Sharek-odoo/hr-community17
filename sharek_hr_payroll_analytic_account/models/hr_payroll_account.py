# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    #
    # def _prepare_line_values(self, line, account_id, date, debit, credit):
    #     res = super(HrPayslip,self)._prepare_line_values(line, account_id, date, debit, credit)
    #     analytic_restrict = self.company_id.restrict_analytic_account
    #     account_type_ids =  self.company_id.account_type_ids
    #     if analytic_restrict:
    #         if not account_type_ids:
    #             raise UserError(_("Analytic account should be restricted to special account types. \n"
    #                               "Please configure account types under payroll settings"))
    #         print ("---------account_type_ids",account_type_ids)
    #         account = self.env['account.account'].browse(account_id)
    #         if not account.account_type in account_type_ids.mapped('account_type'):
    #             res.update({'analytic_distribution': False})
    #
    #     return res
    
    #
    # def _get_existing_lines(self, line_ids, line, account_id, debit, credit):
    #     analytic_restrict = self.company_id.restrict_analytic_account
    #     account_type_ids =  self.company_id.account_type_ids
    #     account = self.env['account.account'].browse(account_id)
    #     if analytic_restrict and not account.account_type in account_type_ids.mapped('account_type'):
    #     # if analytic_restrict :
    #         existing_lines = (
    #         line_id for line_id in line_ids if
    #         line_id['name'] == line.name
    #         and line_id['account_id'] == account_id
    #         # and line_id['analytic_account_id'] == (line.salary_rule_id.analytic_account_id.id or line.slip_id.contract_id.analytic_account_id.id)
    #         and ((line_id['debit'] > 0 and credit <= 0) or (line_id['credit'] > 0 and debit <= 0)))
    #     else:
    #
    #         analytic_account_id = line.salary_rule_id.analytic_account_id.id or line.slip_id.contract_id.analytic_account_id.id
    #         existing_lines = (
    #             line_id for line_id in line_ids if
    #             line_id['name'] == line.name
    #             and line_id['account_id'] == account_id
    #             and (line_id['analytic_distribution'] == {analytic_account_id:100} or line_id['analytic_distribution'] in (False,{}))
    #             # and line_id['analytic_distribution'] == {analytic_account_id:100} or False
    #             and ((line_id['debit'] > 0 and credit <= 0) or (line_id['credit'] > 0 and debit <= 0)))
    #     return next(existing_lines, False)