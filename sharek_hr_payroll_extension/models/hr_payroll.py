# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined

from odoo import models, fields, api, _
from datetime import datetime, date
import logging

from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    state = fields.Selection([
        ('draft', 'New'),
        ('verify', 'Waiting'),
        ('confirm', 'Confirmed'),
        ('approve', 'Approved'),
        ('close', 'Done'),
        ('paid', 'Paid'),
        ('refuse', 'Refused'),
        ('cancel', 'Cancelled')
    ], string='Status', index=True, readonly=True, copy=False, default='draft')

    @api.onchange('date_start')
    def onchange_date_start(self):
        if self.date_start:
            self.name = 'Monthly payroll of ' + (self.date_start).strftime('%B %Y')

    name = fields.Char(default=lambda self: 'Monthly payroll of ' + (date.today()).strftime('%B %Y'))

    def action_confirm(self):
        payslip_confirm_result = self.mapped('slip_ids').filtered(
            lambda slip: slip.state in ['verify']).action_confirm()
        self.write({'state': 'confirm'})
        return payslip_confirm_result

    def action_approve(self):
        for record in self:
            self.action_validate()
            record.write({'state': 'approve'})
        # return payslip_approve_result
    def close_payslip_run(self):
        return self.write({'state': 'close'})
    def action_post(self):
        # payslip_post_result = self.mapped('slip_ids').filtered(lambda slip: slip.state in ['approve']).action_post()
        # payslip_post_result = self.mapped('slip_ids').filtered(lambda slip: slip.state in ['done']).action_post()
        payslip_post_result = self.slip_ids[0].move_id.action_post()
        self.write({'state': 'close'})
        return payslip_post_result

    def action_refuse(self):
        payslip_refuse_result = self.mapped('slip_ids').filtered(
            lambda slip: slip.state not in ['done', 'paid', 'cancel', 'refuse']).action_refuse()
        self.write({'state': 'refuse'})
        return payslip_refuse_result

    def action_cancel(self):
        payslip_cancel_result = self.mapped('slip_ids').filtered(
            lambda slip: slip.state not in ['done', 'paid', 'cancel', 'refuse']).action_payslip_cancel()
        self.write({'state': 'cancel'})
        return payslip_cancel_result

    def action_draft(self):
        payslip_draft_result = self.mapped('slip_ids').filtered(lambda slip: slip.
                                                                state not in ['done', 'paid']).action_payslip_draft()
        self.write({'state': 'draft'})
        return payslip_draft_result


class HRPayslip(models.Model):
    _inherit = 'hr.payslip'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('verify', 'Waiting'),
        ('confirm', 'Confirmed'),
        ('approve', 'Approved'),
        ('done', 'Done'),
        ('paid', 'Paid'),
        ('refuse', 'Refused'),
        ('cancel', 'Cancelled')],
        string='Status', index=True, readonly=True, copy=False,
        default='draft', tracking=True,
        help="""* When the payslip is created the status is \'Draft\'
                \n* If the payslip is under verification, the status is \'Waiting\'.
                \n* If the payslip is confirmed then status is set to \'Done\'.
                \n* When user cancel payslip the status is \'Rejected\'.""")

    def action_payslip_paid(self):
        if any(slip.state != 'done' for slip in self):
            raise UserError(_('Cannot mark payslip as paid if not confirmed.'))
        # self.write({'state': 'paid'})

    def action_confirm(self):
        for record in self:
            record.write({'state': 'confirm'})

    def action_approve(self):
        for record in self:
            record.action_payslip_done()
            record.write({'state': 'approve'})

    def action_post(self):
        for record in self:
            record.move_id.action_post()
            record.write({'state': 'done'})

    def action_refuse(self):
        for record in self:
            record.write({'state': 'refuse'})

    def action_payslip_cancel(self):
        for record in self:
            if not self.env.user._is_system() and self.filtered(lambda slip: slip.state in ['done', 'paid']):
                raise UserError(_("Cannot cancel a payslip that is done."))
            record.move_id.button_cancel()
            record.write({'state': 'cancel'})
            # record.mapped('payslip_run_id').action_close()
