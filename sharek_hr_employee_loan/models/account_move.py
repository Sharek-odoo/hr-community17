# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
from odoo import models, api, fields, _
from odoo.exceptions import UserError, AccessError, ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    loan_installment_ids = fields.Many2many(
        'hr.loan.line',
        string='Loan Installment',
        readonly=False,
        copy=False,
        states={'draft': [('readonly', False)]}
    )

    loan_id = fields.Many2one('hr.loan')

    def action_post(self):
        res = super(AccountMove, self).action_post()
        # todo: check the if amount is less then installment amount then it could not be applicable to pay installment
        for move in self:
            if move.loan_installment_ids:
                move.loan_installment_ids.write({'paid': True})
            if not move.loan_id.loan_lines.filtered(lambda line: line.paid == False):
                move.loan_id.payment_state = 'paid'
        return res

    # @api.constrains('line_ids', 'line_ids.analytic_account_id')
    # def _check_analytic_account_id(self):
    #     for order in self:
    #         for line in order.line_ids:
    #             if order.move_type not in ['out_invoice', 'in_receipt'] and line.analytic_account_id != False:
    #                 raise ValidationError(_('Please Delete Analytic Account From Line.'))
