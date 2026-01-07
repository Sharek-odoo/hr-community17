# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined

from odoo import fields, models, api


class ReligionReligion(models.Model):
    _name = 'religion.religion'
    _description = 'Religion'

    name = fields.Char(string='Name', translate=True)
