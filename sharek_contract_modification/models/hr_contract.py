# -*- coding: utf-8 -*-

from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from datetime import date, timedelta

class HrContractLeaveLog(models.Model):
    _name = 'hr.contract.leave.log'
    _description = 'Leave Log for Trial Period'

    contract_id = fields.Many2one('hr.contract', string="Contract", ondelete='cascade')
    leave_id = fields.Many2one('hr.leave', string="Leave")
    leave_type_id = fields.Many2one(related='leave_id.holiday_status_id', string="Leave Type", store=True)
    date_from = fields.Date(related='leave_id.request_date_from', store=True)
    date_to = fields.Date(related='leave_id.request_date_to', store=True)
    days = fields.Float(string="Days", compute='_compute_days', store=True)
    original_end_trial_period = fields.Date(string="Original End of Trial Period")

    @api.depends('leave_id')
    def _compute_days(self):
        for rec in self:
            rec.days = rec.leave_id.number_of_days_display if rec.leave_id else 0.0


class HrContractInhertit(models.Model):
    _inherit = 'hr.contract'

    contract_type = fields.Selection([('specified', 'Specified Period'), ('unspecified', 'Unspecified Period')],
                                     required=True, default='specified', string="Contract Type Period")
    no_year = fields.Integer(string="No Of Years", default=1)

    need_trial_period = fields.Boolean(string="Needs Trial Period?")
    trial_period = fields.Selection(
        [('without_period', 'Without Period'), ('three_month', '3 Months'), ('six_month', '6 Months')],
        default="without_period")
    trial_extension_months = fields.Integer(string="Trial Duration (Months)", default=0)
    end_trial_period = fields.Date(compute="_compute_end_trial_period",)
    leave_log_ids = fields.One2many('hr.contract.leave.log', 'contract_id', string="Leave Log")
    original_trial_end_date = fields.Date(string="Original Trial End Date Before Leave Extension", readonly=True)


    @api.onchange('contract_type', 'date_start', 'no_year')
    def _onchange_compute_end_date(self):
        for record in self:
            if record.contract_type == 'specified' and record.date_start and record.no_year:
                record.date_end = record.date_start + relativedelta(years=record.no_year) - timedelta(days=1)



    @api.onchange('employee_id')
    def _onchange_employee(self):
        """ func for compute join date of trial period """
        for rec in self:
            rec.date_start = rec.employee_id.join_date


    @api.depends('trial_period', 'date_start', 'trial_extension_months', 'employee_id')
    def _compute_end_trial_period(self):
        Leave = self.env['hr.leave']
        for contract in self:
            if not contract.need_trial_period:
                contract.end_trial_period = contract.date_end
                continue

            base_months = 0
            if contract.trial_period == 'three_month':
                base_months = 3
            elif contract.trial_period == 'six_month':
                base_months = 6

            total_months = base_months + contract.trial_extension_months

            if contract.date_start and total_months > 0:
                # Step 1: Compute base end date without leaves
                base_trial_end = contract.date_start + relativedelta(months=total_months)

                # Step 2: Save it as original (snapshot before leave extension)
                contract.original_trial_end_date = base_trial_end

                # Step 3: Find validated leaves overlapping trial period
                leaves = Leave.search([
                    ('employee_id', '=', contract.employee_id.id),
                    ('state', '=', 'validate'),
                    ('request_date_from', '<=', base_trial_end),
                    ('request_date_to', '>=', contract.date_start),
                ])

                # Step 4: Remove old logs
                contract.leave_log_ids.unlink()

                total_leave_days = 0.0
                for leave in leaves:
                    days = leave.number_of_days_display or 0.0
                    total_leave_days += days
                    self.env['hr.contract.leave.log'].create({
                        'contract_id': contract.id,
                        'leave_id': leave.id,
                        'original_end_trial_period': base_trial_end,
                    })

                # Step 5: Update actual end date
                contract.end_trial_period = base_trial_end + timedelta(days=total_leave_days)

            else:
                contract.end_trial_period = contract.date_end



    date_end = fields.Date(
        'End Date',
        tracking=True,
        default=lambda self: date.today() + relativedelta(years=1),
        help="End date of the contract (if it's a fixed-term contract)."
    )

    # @api.onchange('start_date')
    # def _onchange_start_date(self):
    #     if self.start_date:
    #         self.date_end = self.start_date + timedelta(days=365)


