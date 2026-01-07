from odoo import models, fields,_

class AcademicYear(models.Model):
    _name = 'academic.year'


    name = fields.Char(string="Academic Year")

    