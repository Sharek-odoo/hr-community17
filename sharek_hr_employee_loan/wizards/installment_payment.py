# -*- coding: utf-8 -*-

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class HrLoanPayment(models.TransientModel):
    _name = 'hr.loan.payment.wizard'
    _description = "Loan installments payment"

    installment_ids = fields.Many2many('hr.loan.line', domain="[('paid', '=', False), ('loan_id', '=', loan_id)]")
    payment_date = fields.Date(string="Payment Date", default=fields.Date.today(),
                               required=True, help="Date of the payment")
    journal_id = fields.Many2one('account.journal', string='Payment Journal', domain="[('company_id', '=', company_id),"
                                                                                     "('type', 'in', ('bank', 'cash'))]")
    amount = fields.Float(string='Payment Amount', compute='_compute_amount')
    ref = fields.Char(string='Memo')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    partner_id = fields.Many2one('res.partner', string='Partner')
    loan_id = fields.Many2one("hr.loan", string="Loan", required=False, )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get('active_id') and self.env.context.get('active_model') == 'hr.loan':
            loan = self.env['hr.loan'].browse(self.env.context.get('active_id'))
            res.update({'loan_id': loan.id,
                        'partner_id' : loan.employee_id.user_partner_id.id,
                        })
        return res

    @api.depends('installment_ids.amount')
    def _compute_amount(self):
        self.amount = sum(self.installment_ids.mapped('amount'))
    #
    # def action_create_payments(self):
    #     payment_vals = self._create_payment_vals_from_wizard()
    #     payment = self.env['account.payment'].create(payment_vals)
    #     if payment:
    #         payment.action_post()

    def action_create_payments(self):
        debit_account_id = self.loan_id.treasury_account_id.id
        credit_account_id = self.loan_id.employee_account_id.id
        amount = self.amount
        debit_vals = {
            'name': self.loan_id.employee_id.name,
            'account_id': debit_account_id,
            'journal_id': self.journal_id.id,
            'date': self.payment_date,
            'debit': amount > 0.0 and amount or 0.0,
            'credit': amount < 0.0 and -amount or 0.0,
            'loan_id': self.loan_id.id,
        }
        credit_vals = {
            'name': self.loan_id.employee_id.name,
            'account_id': credit_account_id,
            'journal_id': self.journal_id.id,
            'partner_id':self.partner_id.id,
            'date': self.payment_date,
            'debit': amount < 0.0 and -amount or 0.0,
            'credit': amount > 0.0 and amount or 0.0,
            'loan_id': self.loan_id.id,
        }
        vals = {
            'date': self.payment_date,
            'ref': self.ref,
            'journal_id': self.journal_id.id,
            'partner_id': self.partner_id.id,
            'loan_installment_ids': self.installment_ids,
            'loan_id': self.loan_id.id,
            'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
        }
        move = self.env['account.move'].create(vals)
        move.action_post()
        # payment_vals = {
        #     'date': self.payment_date,
        #     'amount': self.amount,
        #     'payment_type': 'inbound',
        #     'partner_type': 'supplier',
        #     'ref': self.ref,
        #     'journal_id': self.journal_id.id,
        #     'partner_id': self.partner_id.id,
        #     'loan_installment_ids': self.installment_ids,
        #     'loan_id': self.installment_ids.loan_id.id,
        # }
        # return payment_vals
