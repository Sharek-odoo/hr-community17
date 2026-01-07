# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class EmployeeLoanReportWizard(models.TransientModel):
    _name = 'employee.loan.report.wizard'
    _description = "Employee Loan Report Wizard"

    date_from = fields.Date(string="Date From", required=False, )
    date_to = fields.Date(string="Date To", required=False)
    employee_ids = fields.Many2many("hr.employee", string="Employee", required=False)

    @api.constrains('date_from', 'date_to')
    def _check_rule_date_from(self):
        if any(applicability for applicability in self
               if applicability.date_to and applicability.date_from
                  and applicability.date_to < applicability.date_from):
            raise ValidationError(_('The Date From must be before the Date To'))

    def get_report(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': self.read(
                ['date_from', 'date_to', 'employee_ids'])[0]
        }
        return self.env.ref('sharek_hr_employee_loan.action_sharek_hr_employee_loan_report').report_action(self, data=data)
