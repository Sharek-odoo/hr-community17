# -*- coding: utf-8 -*-

from odoo import models, fields, api


class sharek_earning_extend(models.Model):
    _inherit = "other.earnings"


    type = fields.Selection([('allowance', 'Allowance'), ('other_allowance', 'Other Allowance'),
                            ('deduction', 'Disciplinary action Deduction'),
                            ('other_deduction', 'Other Deductions'),
                            ('gosi', 'GOSI Deduction')], string="Type", default='')
    AMOUNT_TYPES = [
        ("percentage", "Percentage"),
        ("amount", "Amount"),
        ("day", "Days")
    ]

    base_on = fields.Selection(AMOUNT_TYPES, string="Base On", default="day")
    percentage = fields.Float(string="Percentage %")
    no_od_day = fields.Float(string="No Of Days")

    @api.depends('base_on', 'percentage', 'no_od_day', 'amount')
    def compute_amount(self):
        for rec in self:
            for line in  rec.earnings_ids:
                salary = line.employee_id.contract_id.total_gross_salary or 0.0
                line.base_on = rec.base_on
                line.date = rec.start_date
                if rec.base_on == 'percentage':
                    line.percentage = rec.percentage
                    line.amount = (line.percentage/100) * (salary / 30)
                elif  rec.base_on == 'day':
                    line.no_od_day = rec.no_od_day
                    line.amount = line.no_od_day * (salary / 30)
                else:
                    line.amount = rec.amount

class OtherEarningsLine(models.Model):
    _inherit = "other.earnings.line"

    AMOUNT_TYPES = [
        ("percentage", "Percentage"),
        ("amount", "Amount"),
        ("day", "Days")
    ]

    base_on = fields.Selection(
        AMOUNT_TYPES,
        string="Base On",
        default="day",
        store=True,  # Required for front-end use
        readonly=True  # Optional: since it's inherited
    )

    percentage = fields.Float(string="Percentage %")
    no_od_day = fields.Float(string="No Of Days")

class HRPayrollAllow(models.Model):
    _inherit = 'hr.payslip'

    other_deduction = fields.Float(compute="_compute_other_deduction_amount")
    gosi_deduction = fields.Float(compute="_compute_gosi_amount",)
    other_allowance = fields.Float(compute="_compute_other_amount")

    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_other_deduction_amount(self):
        for pay in self:
            amount = 0.0
            amount_line = self.env['other.earnings.line'].search([
                ('employee_id', '=', pay.employee_id.id),
                ('date', '>=', pay.date_from),
                ('date', '<=', pay.date_to),
                ('earnings_line_id.state', '=', 'confirm'),
                ('earnings_line_id.earnings_type', '=', 'payroll'),
                ('earnings_line_id.type', '=', 'other_deduction')
            ])
            for rec in amount_line:
                amount += rec.amount
            pay.other_deduction = amount  # ✅ Assign per payslip


    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_gosi_amount(self):
        for pay in self:
            amount = 0.0
            amount_line = self.env['other.earnings.line'].search([
                ('employee_id', '=', pay.employee_id.id),
                ('date', '>=', pay.date_from),
                ('date', '<=', pay.date_to),
                ('earnings_line_id.state', '=', 'confirm'),
                ('earnings_line_id.earnings_type', '=', 'payroll'),
                ('earnings_line_id.type', '=', 'gosi')
            ])
            for rec in amount_line:
                amount += rec.amount
            pay.gosi_deduction = amount


    @api.depends('employee_id', 'date_from', 'date_to')
    def _compute_other_amount(self):
        for pay in self:
            amount = 0.0
            print("\n\n\n\n")
            print("amount 1",amount)
            amount_line = self.env['other.earnings.line'].search([
                ('employee_id', '=', pay.employee_id.id),
                ('date', '>=', pay.date_from),
                ('date', '<=', pay.date_to),
                ('earnings_line_id.state', '=', 'confirm'),
                ('earnings_line_id.earnings_type', '=', 'payroll'),
                ('earnings_line_id.type', '=', 'other_allowance')
            ])
            print("earn line",amount_line)
            for rec in amount_line:

                amount += rec.amount
                print("amount in line for",amount)
            pay.other_allowance = amount  # ✅ assign per payslip
            print("pay.other_allowance",pay.other_allowance)
            print("pay employee",pay.employee_id.name)


