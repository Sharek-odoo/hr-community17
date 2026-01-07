# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
from odoo import models, fields

class HrApplicantInherit(models.Model):
    _inherit = 'hr.applicant'

    years_of_experience = fields.Integer("Years of Experience", required=True)
    notice_period = fields.Char("Notice Period", required=True)
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ], string="Gender", required=True)
    certificate_two = fields.Selection([
        ('primary', 'Primary School'),
        ('middle', 'Middle School'),
        ('high', 'High School'),
        ('diploma', 'Diploma'),
        ('bachelor', 'Bachelor'),
        ('master', 'Master'),
        ('phd', 'PhD'),
        ('other', 'Other'),
    ], string="Certificate Level", required=True)
    city_residence = fields.Many2one(
        'res.country.state',
        string="City of Residence",
        required=True
    )
