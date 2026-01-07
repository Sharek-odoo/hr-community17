# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class GradeGrade(models.Model):
    _name = "grade.grade"
    _description = "Grade"

    name = fields.Char()
    hr_percentage = fields.Float('Transportation Percentage %')
    transport_allowance = fields.Monetary(string="Transportation Allowance", tracking=True)
    description = fields.Text()
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Currency", store=True)
    timeoff_days = fields.Integer('Timeoff Days')
    educ_allowance = fields.Float(string="Education Allowance")

class HrEmployee(models.Model):

    _inherit = "hr.employee"

    grade_id = fields.Many2one("grade.grade", "Grade")
    department_manager_display = fields.Char(
        string='Department – Manager',
        compute='_compute_department_manager_display',
        store=True,
        index=True
    )

    @api.depends(
        'department_id',
        'department_id.name',
        'department_id.manager_id',
        'department_id.manager_id.arabic_name'
    )
    def _compute_department_manager_display(self):
        # Force Arabic language context
        arabic_ctx = dict(self.env.context, lang='ar_001')

        for emp in self:
            if emp.department_id:
                dept = emp.department_id.with_context(arabic_ctx)
                dept_name = dept.name or ''
                manager_name = emp.department_id.manager_id.arabic_name or ''

                emp.department_manager_display = (
                    f"{dept_name} – {manager_name}"
                    if manager_name else dept_name
                )
            else:
                emp.department_manager_display = False