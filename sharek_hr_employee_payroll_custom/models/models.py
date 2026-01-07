# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined

from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    direct_supervisor = fields.Many2one('hr.employee',string='Direct Supervisor')
    under_company = fields.Boolean(string='Under Company')
    iban = fields.Char('IBAN',size=21)


# class HrContract(models.Model):
#     _inherit = 'hr.contract'
#
#
#     @api.onchange('structure_type_id')
#     def change_struct_id(self):
#     	self.struct_id = self.structure_type_id.default_struct_id.id
