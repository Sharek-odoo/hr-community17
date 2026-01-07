# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined

from odoo import models, fields, api


class HRFamily(models.Model):
    _name = 'hr.family'
    _description = 'Employee Family Member'

    name = fields.Char('Name')
    relationship = fields.Selection([('father', 'Father'), ('mother', 'Mother'), ('wife', 'Wife'), ('son', 'Son'), ('daughter', 'Daughter'), ('other', 'Other')], 'Relationship')
    id_no = fields.Char('ID Number')
    birth_date = fields.Date('Date of Birth')
    phone = fields.Char('Phone')
    is_emergency = fields.Boolean('Emergency')
    employee_id = fields.Many2one('hr.employee')


class HREmployee(models.Model):
    _inherit = 'hr.employee'

    family_ids = fields.One2many('hr.family', 'employee_id', 'Family')
    sponsor = fields.Char('Sponsor')
    nal = fields.Char('Nal')


