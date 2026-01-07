# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class HrAttendanceRule(models.Model):
    _name = 'hr.attendance.rule'
    _description = 'Hr Attendance Rules'

    name = fields.Char(required=True, translate=True)
    employee_id = fields.Many2one('hr.employee', string='Employee')
    department_id = fields.Many2one('hr.department', string='Department')
    company_id = fields.Many2one('res.company', string='Company')
    active = fields.Boolean(string='Active', default=True)
    rule_type = fields.Selection([('employee', 'By Employee'), ('department', 'By Department'),
                                  ('company', 'By Company')], default='company', string='Mode',
                                 required=True)
    allow_late_in = fields.Integer(string='Allow Late-In', required=True)
    allow_early_out = fields.Integer(string='Allow Early-Out', required=True)
    minimum_deduct_minutes = fields.Integer(string='Minimum Minutes To Deduct', required=True, default=30)
    overtime_calculate = fields.Boolean(string='Calculate Overtime')
    overtime_start = fields.Float(string='Overtime Start')
    overtime_end = fields.Float(string='Overtime End')
    max_overtime_duration = fields.Integer(string='Max OT Duration')

    @api.onchange('overtime_start', 'overtime_end')
    def onchange_overtime_duration(self):
        if self.overtime_start and self.overtime_end:
            self.max_overtime_duration = (self.overtime_end - self.overtime_start) * 60

    @api.constrains('active')
    def check_deplicate_rule(self):
        for record in self:
            if record.rule_type == 'company':
                existing_company_rules = self.env['hr.attendance.rule'].search([('rule_type', '=', 'company'),
                                                                                ('company_id', '=',
                                                                                 record.company_id.id),
                                                                                ('id', '!=', record.id)])
                if existing_company_rules:
                    raise ValidationError(_("You can't define multiple rules for the same company\n"
                                            "please archive active rules in order to create new one"))
            elif record.rule_type == 'department':
                existing_department_rules = self.env['hr.attendance.rule'].search([('rule_type', '=', 'department'),  ('id', '!=', record.id),
                                                                                   ('department_id', '=', record.department_id.id)])
                if existing_department_rules:
                    raise ValidationError(_("You can't define multiple rules for the same department\n"
                                            "please archive active rules in order to create new one"))
            elif record.rule_type == 'employee':
                existing_department_rules = self.env['hr.attendance.rule'].search(
                    [('rule_type', '=', 'employee'), ('id', '!=', record.id),
                     ('employee_id', '=', record.employee_id.id)])
                if existing_department_rules:
                    raise ValidationError(_("You can't define multiple rules for the same employee\n"
                                            "please archive active rules in order to create new one"))
            else:
                pass
