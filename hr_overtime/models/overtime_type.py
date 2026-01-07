# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class HrOverTimeType(models.Model):
    _name = 'overtime.type'
    _description = "HR Overtime Type"

    name = fields.Char('Name', required=1)
    category = fields.Selection([('workday', 'Workday'),
                                 ('weekend', 'Weekend'),
                                 ('holiday', 'Holiday'),
                                 ], defautl='workday', string='Category', required=True)
    hour_rate = fields.Float(string='Hour Rate', required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    # calculation_option = fields.Selection([('basic', 'Basic Salary'),
    #                                        ('gross', 'Gross Salary'),
    #                                        ('both', 'Basic + Gross')],
    #                                       default='both', string='Calculate Based On')
    @api.onchange('category')
    def onchange_overtime_category(self):
        overtime = self.category == 'workday' and self.company_id.weekday_hour_rate or \
                   self.category == 'weekend' and self.company_id.weekend_hour_rate or \
                   self.category == 'holiday' and self.company_id.holiday_hour_rate
        self.hour_rate = overtime
