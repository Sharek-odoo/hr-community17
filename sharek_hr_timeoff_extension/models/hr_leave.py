# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
from odoo import models, fields, api, _
# from odoo.addons.resource.models.resource import HOURS_PER_DAY
from odoo.exceptions import ValidationError,UserError
from datetime import timedelta, datetime, time,date
from math import ceil
from odoo.addons.resource.models.utils import HOURS_PER_DAY


class HolidaysRequest(models.Model):
    _inherit = "hr.leave"

    number = fields.Char(index=True, readonly=True)
    attachment_ids = fields.Many2many('ir.attachment', string='Supporting Documents')
    balance = fields.Float(compute="_compute_employee_balance")
    required_delegation = fields.Boolean(related='holiday_status_id.required_delegation')
    required_ticket = fields.Boolean(related='holiday_status_id.required_ticket')
    delegated_id = fields.Many2one('hr.employee', string='Delegation')
    balance_after_request = fields.Float(
        string='Balance After Request',
        compute='_compute_balance_after_request',
    )

    @api.depends('employee_id', 'number_of_days', 'holiday_status_id')
    def _compute_balance_after_request(self):
        today = fields.Date.today()
        year_start = date(today.year, 1, 1)
        year_end = date(today.year, 12, 31)

        for rec in self:
            rec.balance_after_request = 0.0

            if not rec.employee_id or not rec.holiday_status_id:
                continue

            employee = rec.employee_id

            # 1️⃣ Allocations in current year (same leave type)
            allocations = self.env['hr.leave.allocation'].search([
                ('employee_id', '=', employee.id),
                ('holiday_status_id', '=', rec.holiday_status_id.id),
                ('state', '=', 'validate'),
                ('date_from', '<=', year_end),
                ('date_to', '>=', year_start),
            ])

            allocated_days = sum(allocations.mapped('number_of_days'))

            domain = [
                ('employee_id', '=', employee.id),
                ('holiday_status_id', '=', rec.holiday_status_id.id),
                ('state', '=', 'validate'),
                ('request_date_from', '>=', year_start),
                ('request_date_to', '<=', year_end),
            ]

            # ✅ Exclude current record ONLY if it is saved in DB
            if rec.id and isinstance(rec.id, int):
                domain.append(('id', '!=', rec.id))

            leaves = self.env['hr.leave'].search(domain)

            taken_days = sum(leaves.mapped('number_of_days'))

            current_balance = allocated_days - taken_days
            requested_days = rec.number_of_days or 0.0

            rec.balance_after_request = max(current_balance - requested_days, 0.0)


    @api.model_create_multi
    @api.returns('self', lambda value: value.id)
    def create(self, vals_list):
        for vals in vals_list:
            employee = self.env['hr.employee'].browse(vals['employee_id'])
            # vals['number'] = self.env['ir.sequence'].with_company(employee.company_id).next_by_code(self._name)
            vals['number'] = self.env['ir.sequence'].next_by_code(self._name)
        return super(HolidaysRequest, self).create(vals_list)

    # def _get_number_of_days(self, date_from, date_to, employee_id):
    #     res = super(HolidaysRequest, self)._get_number_of_days(date_from, date_to, employee_id)
    #     if self.holiday_status_id.calc_type == 'calendar':
    #         days = (date_to - date_from).days + 1
    #         print(days, "*****************", res)
    #         return {'days': days, 'hours': HOURS_PER_DAY * days}
    #     return res

    # @api.depends('date_from', 'date_to', 'employee_id')
    # def _compute_number_of_days(self):
    #     for holiday in self:
    #         if holiday.date_from and holiday.date_to:
    #             holiday.number_of_days = \
    #             holiday._get_number_of_days(holiday.date_from, holiday.date_to, holiday.employee_id.id)['days']
    #             if holiday.holiday_status_id.calc_type == 'calendar':
    #                 holiday.number_of_days = (holiday.date_to - holiday.date_from).days + 1
    #         else:
    #             holiday.number_of_days = 0


    def _get_duration(self, check_leave_type=True, resource_calendar=None):
        self.ensure_one()

        # --- Custom logic for calc_type = calendar ---
        if self.holiday_status_id.calc_type == 'calendar':
            if not self.date_from or not self.date_to:
                return (0, 0)
            # full calendar days count
            days = (self.date_to.date() - self.date_from.date()).days + 1
            # hours = days * standard hours per day (or you could just set 0)
            hours = days * HOURS_PER_DAY
            return (days, hours)

        # --- Otherwise, fallback to Odoo standard ---
        return super(HolidaysRequest, self)._get_duration(check_leave_type=check_leave_type, resource_calendar=resource_calendar)


    # @api.depends('employee_id')
    # def _compute_employee_balance(self):
    #     today = fields.Date.today()
    #     year_start = date(today.year, 1, 1)
    #     year_end = date(today.year, 12, 31)
    #
    #     for rec in self:
    #         rec.balance = 0.0
    #         if not rec.employee_id:
    #             continue
    #
    #         employee = rec.employee_id
    #
    #         # 1️⃣ Allocated leaves (current year)
    #         allocations = self.env['hr.leave.allocation'].search([
    #             ('employee_id', '=', employee.id),
    #             ('state', '=', 'validate'),
    #             ('date_from', '<=', year_end),
    #             ('date_to', '>=', year_start),
    #         ])
    #
    #         allocated_days = sum(allocations.mapped('number_of_days'))
    #
    #         # 2️⃣ Taken leaves (current year)
    #         leaves = self.env['hr.leave'].search([
    #             ('employee_id', '=', employee.id),
    #             ('state', '=', 'validate'),
    #             ('request_date_from', '>=', year_start),
    #             ('request_date_to', '<=', year_end),
    #         ])
    #
    #         taken_days = sum(leaves.mapped('number_of_days'))
    #
    #         # 3️⃣ Remaining balance
    #         rec.balance = allocated_days - taken_days

    @api.depends('employee_id', 'holiday_status_id')
    def _compute_employee_balance(self):
        today = fields.Date.today()
        year_start = date(today.year, 1, 1)
        year_end = date(today.year, 12, 31)

        for rec in self:
            rec.balance = 0.0

            if not rec.employee_id or not rec.holiday_status_id:
                continue

            # ❗ Only calculate for Annual leave
            if rec.holiday_status_id.timeoff_normal_type != 'annual':
                continue

            employee = rec.employee_id

            # 1️⃣ Allocated annual leaves (current year)
            allocations = self.env['hr.leave.allocation'].search([
                ('employee_id', '=', employee.id),
                ('holiday_status_id', '=', rec.holiday_status_id.id),
                ('state', '=', 'validate'),
                ('date_from', '<=', year_end),
                ('date_to', '>=', year_start),
            ])

            allocated_days = sum(allocations.mapped('number_of_days'))

            # 2️⃣ Taken annual leaves (current year)
            leaves = self.env['hr.leave'].search([
                ('employee_id', '=', employee.id),
                ('holiday_status_id', '=', rec.holiday_status_id.id),
                ('state', '=', 'validate'),
                ('request_date_from', '>=', year_start),
                ('request_date_to', '<=', year_end),
            ])

            taken_days = sum(leaves.mapped('number_of_days'))

            # 3️⃣ Remaining balance
            rec.balance = allocated_days - taken_days

    @api.constrains('employee_id', 'holiday_status_id', 'start_date', 'end_date')
    def _check_negative_leave(self):
        for record in self:
            if record.state not in ['draft', 'cancel',
                                    'refuse'] and record.holiday_status_id.allow_negative:
                if 0 < record.holiday_status_id.negative_limit < record.number_of_days:
                    raise ValidationError(_('You cannot take a(an) %s leave more than %s day(s).' % (
                        record.holiday_status_id.name, record.holiday_status_id.negative_limit)))

    @api.onchange('employee_id')
    def _onchange_employee(self):
        """override onchange of employee to add domain on holiday_status_id based on emp_type of employee"""
        domain = {}
        type_ids = []
        if self.employee_id and self.employee_id.gender:
            leave_types = self.env['hr.leave.type'].search(
                ['|', ('for_specific_gender', '=', False), ('gender', '=', self.employee_id.gender)])
            type_ids += leave_types and leave_types.ids
        if self.employee_id and self.employee_id.religion_id:
            leave_types = self.env['hr.leave.type'].search(
                ['|', ('religion_ids', '=', False), ('religion_ids', 'in', self.employee_id.religion_id.ids)])
            type_ids += leave_types and leave_types.ids

        if len(type_ids) > 0:
            domain.update({'holiday_status_id': [('id', 'in', list(set(type_ids)))]})
            return {'domain': domain}
