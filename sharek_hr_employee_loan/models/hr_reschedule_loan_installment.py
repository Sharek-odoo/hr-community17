# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined

from odoo import models, fields, api, _
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import ValidationError
from dateutil.relativedelta import *


class HrRescheduleLoanInstallment(models.Model):
    _name = 'hr.reschedule.loan.installment'
    _inherit = ['mail.thread']
    _description = "Employee Loan Installment Rescheduling"

    name = fields.Char('Reason', required=True, tracking=True)
    loan_id = fields.Many2one('hr.loan', 'Loan', tracking=True)
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True,
                                  default=lambda self: self.env['hr.employee'].get_employee(), tracking=True)
    date = fields.Date('Date', required=True, default=fields.Date.today, tracking=True)
    installment_id = fields.Many2one('hr.loan.line')
    old_date = fields.Date(string="Old Payment Date", readonly=True, related='installment_id.date',
                           help="Date of the payment")
    new_date = fields.Date(string="New Payment Date", required=True, help="Date of the payment")
    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', 'Confirm'),
                              ('refuse', 'Refused'),
                              ('approve', 'Approved'),
                              ('cancel', 'Cancelled')], string="Status",
                             required=True, default='draft', tracking=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=False,
                                 default=lambda self: self.env.company)

    def confirm_request(self):
        """
            sent the status of skip installment request in Confirm state
        """
        self.ensure_one()
        self.state = 'confirm'

    def approve_request(self):
        """
            sent the status of skip installment request in confirm state
        """
        self.ensure_one()
        if self.loan_id.state == 'approve':
            installments = self.loan_id.loan_lines.filtered(lambda ins: ins.paid == False and ins.date > self.installment_id.date)
            for line in installments:
                due_date = line.date + relativedelta(months=+1)
                line.write({'date': due_date})
            end_date = self.installment_id.date + relativedelta(months=+1)
            self.installment_id.write({'date': end_date})
            self.write({'state': 'approve'})
        else:
            raise ValidationError(_('You should approve related loan first'))

    def refuse_request(self):
        """
            sent the status of skip installment request in refuse state
        """
        self.ensure_one()
        self.state = 'refuse'

    def set_to_draft(self):
        """
            sent the status of skip installment request in Set to Draft state
        """
        self.ensure_one()
        self.state = 'draft'

    def set_to_cancel(self):
        """
            sent the status of skip installment request in cancel state
        """
        self.ensure_one()
        self.state = 'cancel'

    def unlink(self):
        """
            To remove the record, which is not in 'draft' and 'cancel' states
        """
        for rec in self:
            if rec.state not in ['draft', 'cancel']:
                raise ValidationError(_('You cannot delete a request to skip installment which is in %s state.')%(rec.state))
        return super(HrRescheduleLoanInstallment, self).unlink()
