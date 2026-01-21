# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined

from odoo import models, fields, api, _
# from odoo.addons.resource.models.resource import HOURS_PER_DAY
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class HolidaysAllocation(models.Model):
    _inherit = "hr.leave.allocation"
    last_update = fields.Date('Last Update')
    transfered = fields.Boolean(string="Transferred from Another Year")

    def _set_accrual_allocation(self):
        contracts = self.env['hr.contract'].search([('state', '=', 'open')])
        for contract in contracts:
            previous_allocation = self.env['hr.leave.allocation'].search([('employee_id', '=', contract.employee_id.id),
                                                                          ('holiday_status_id', '=',
                                                                           contract.timeoff_type.id),
                                                                          ('state', '=', 'validate')])
            previous_balance = self.env['hr.leave.balance'].search([('employee_id', '=', contract.employee_id.id),
                                                                    ('leave_type', '=', contract.timeoff_type.id)])
            today = fields.Date.today()
            daily_balance = contract.timeoff_days / 360

            if not previous_allocation and daily_balance > 0:
                delta = today - contract.employee_id.join_date
                number_of_days = daily_balance * (delta.days+1)
                self.env['hr.leave.allocation'].sudo().create({
                    'name': 'Allocation for %s' % contract.employee_id.name,
                    'holiday_status_id': contract.timeoff_type.id,
                    'allocation_type': 'regular',
                    # 'start_date': fields.Date.today(),
                    # 'number_per_interval': number_of_days,
                    'number_of_days': number_of_days,
                    'last_update': today,
                    # 'unit_per_interval': 'days',
                    # 'interval_number': 1,
                    # 'interval_unit': 'days',
                    'holiday_type': 'employee',
                    'employee_id': contract.employee_id.id,
                    'state': 'validate'})

            if previous_allocation and daily_balance > 0:
                delta = today - previous_allocation.last_update
                number_of_days = daily_balance * delta.days
                if number_of_days > 0:
                    previous_allocation.number_of_days = previous_allocation.number_of_days + number_of_days
                    previous_allocation.last_update = today

            if not previous_balance:
                self.env['hr.leave.balance'].create({
                    'employee_id': contract.employee_id.id,
                    'leave_type': contract.timeoff_type.id,
                })
