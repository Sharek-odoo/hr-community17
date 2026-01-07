# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError


class HrLoanReschedule(models.TransientModel):
    _name = 'reschedule.installment.wizard'
    _description = "Rescheduling Loan installments"

    installment_id = fields.Many2one('hr.loan.line', domain=[('paid', '=', False)])
    old_date = fields.Date(string="Old Payment Date", readonly=True, related='installment_id.date',
                           help="Date of the payment")
    new_date = fields.Date(string="New Payment Date", required=True, help="Date of the payment",
                           compute="_compute_due_date")
    reason = fields.Char('Reason of Postpone', required=True, tracking=True)
    loan_id = fields.Many2one("hr.loan", string="Loan", related='installment_id.loan_id')
    @api.depends('old_date')
    def _compute_due_date(self):
        self.new_date = self.old_date + relativedelta(months=1)

    def rescedule(self):
        vals = {
            'name': self.reason,
            'loan_id': self.installment_id.loan_id.id,
            'installment_id': self.installment_id.id,
            'employee_id': self.installment_id.loan_id.employee_id.id,
            'old_date': self.old_date,
            'new_date': self.new_date

        }

        reschedule_request = self.env['hr.reschedule.loan.installment'].create(vals)

