# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined

# from odoo import models, fields, api


# class sharek_hr_required_fields(models.Model):
#     _name = 'sharek_hr_required_fields.sharek_hr_required_fields'
#     _description = 'sharek_hr_required_fields.sharek_hr_required_fields'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
