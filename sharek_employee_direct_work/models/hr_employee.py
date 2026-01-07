# -*- coding: utf-8 -*-

from odoo import models, fields, api


class EmployeeDirectWork(models.Model):
    _inherit = 'hr.employee'

    direct_work_date = fields.Date('Sart Work Date',tracking=True,)
