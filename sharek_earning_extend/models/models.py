# -*- coding: utf-8 -*-

from odoo import models, fields, api


class sharek_earning_extend(models.Model):
    _inherit = "other.earnings"

    type = fields.Selection(selection_add=[('reward_allowance', 'Reward Allowance'),
    	('target1_allowance', 'Target 1 Allowance')
    	,('target2_allowance', 'Target 2 Allowance')
    	,('gosi', 'GOSI Deduction')
    	,('other_allowance', 'Other Allowance')],
    	string="Type", default='')

class HRPayrollAllow(models.Model):
    _inherit = 'hr.payslip'


    reward_allowance = fields.Float(compute="_compute_reward_amount")
    target1_allowance = fields.Float(compute="_compute_target1_amount")
    target2_allowance = fields.Float(compute="_compute_target2_amount")
    gosi_deduction = fields.Float(compute="_compute_gosi_amount")
    other_allowance = fields.Float(compute="_compute_other_amount")

    def _compute_reward_amount(self):
        amount = 0.0
        for pay in self:
            amount_line = self.env['other.earnings.line'].search([('employee_id','=',pay.employee_id.id),
                ('date','>=',pay.date_from),('date','<=',pay.date_to),('earnings_line_id.state','=','confirm'),('earnings_line_id.earnings_type','=','payroll'),('earnings_line_id.type','=','reward_allowance')])
            for rec in amount_line:
                amount += rec.amount
        self.reward_allowance = amount
    def _compute_target1_amount(self):
        amount = 0.0
        for pay in self:
            amount_line = self.env['other.earnings.line'].search([('employee_id','=',pay.employee_id.id),
                ('date','>=',pay.date_from),('date','<=',pay.date_to),('earnings_line_id.state','=','confirm'),('earnings_line_id.earnings_type','=','payroll'),('earnings_line_id.type','=','target1_allowance')])
            for rec in amount_line:
                amount += rec.amount
        self.target1_allowance = amount
    def _compute_target2_amount(self):
        amount = 0.0
        for pay in self:
            amount_line = self.env['other.earnings.line'].search([('employee_id','=',pay.employee_id.id),
                ('date','>=',pay.date_from),('date','<=',pay.date_to),('earnings_line_id.state','=','confirm'),('earnings_line_id.earnings_type','=','payroll'),('earnings_line_id.type','=','target2_allowance')])
            for rec in amount_line:
                amount += rec.amount
        self.target2_allowance = amount
    def _compute_gosi_amount(self):
        amount = 0.0
        for pay in self:
            amount_line = self.env['other.earnings.line'].search([('employee_id','=',pay.employee_id.id),
                ('date','>=',pay.date_from),('date','<=',pay.date_to),('earnings_line_id.state','=','confirm'),('earnings_line_id.earnings_type','=','payroll'),('earnings_line_id.type','=','gosi')])
            for rec in amount_line:
                amount += rec.amount
        self.gosi_deduction = amount
    def _compute_other_amount(self):
        amount = 0.0
        for pay in self:
            amount_line = self.env['other.earnings.line'].search([('employee_id','=',pay.employee_id.id),
                ('date','>=',pay.date_from),('date','<=',pay.date_to),('earnings_line_id.state','=','confirm'),('earnings_line_id.earnings_type','=','payroll'),('earnings_line_id.type','=','other_allowance')])
            for rec in amount_line:
                amount += rec.amount
        self.other_allowance = amount