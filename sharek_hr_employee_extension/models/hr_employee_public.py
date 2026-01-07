# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined

from odoo import models, fields


class HREmployee (models.Model):
    _inherit = 'hr.employee.public'
        
    employee_no = fields.Char(string='Employee Company ID', readonly=True) 
