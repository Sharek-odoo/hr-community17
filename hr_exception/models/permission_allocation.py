# -*- coding: utf-8 -*-

from odoo import models, fields

class PermissionAllocation(models.Model):
    _name = 'permission.allocation'
    _description = 'Permission Hour Allocation'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, unique=True)
    hour_balance = fields.Float(string="Monthly Hour Balance", required=True)
