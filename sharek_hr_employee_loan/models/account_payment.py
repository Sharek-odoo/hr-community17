# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined

from odoo import models, fields, api, _


class AccountPayment(models.Model):
    _inherit = 'account.payment'
    _description = 'account.payment'

    def action_post(self):
        res = super(AccountPayment, self).action_post()
        # todo: check the if amount is less then installment amount then it could not be applicable to pay installment
        for payment in self:
            if payment.loan_installment_ids:
                payment.loan_installment_ids.write({'paid': True})
            if not payment.loan_id.loan_lines.filtered(lambda line: line.paid ==False):
                payment.loan_id.payment_state = 'paid'
        return res

    loan_installment_ids = fields.Many2many(
        'hr.loan.line',
        string='Loan Installment',
        readonly=False,
        copy=False,
        states={'draft': [('readonly', False)]}
    )
    loan_id = fields.Many2one('hr.loan')
