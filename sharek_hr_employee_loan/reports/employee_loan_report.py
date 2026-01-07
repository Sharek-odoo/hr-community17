# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
from odoo import api, fields, models


class EmployeeLoanReport(models.AbstractModel):
    _name = 'report.sharek_hr_employee_loan.sharek_hr_employee_loan_template'
    _description = 'Employee Loan Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        date_from = data['form']['date_from']
        date_to = data['form']['date_to']
        employee_ids = data['form']['employee_ids']

        domain = [('state', '=', 'approve')]
        employees_list = []
        employee_data = []
        doc = []
        # employee_data = []
        if date_from:
            domain.append(('date', '>=', date_from))
        if date_to:
            domain.append(('date', '<=', date_to))
        if employee_ids:
            domain.append(('employee_id', 'in', employee_ids))
        loan_obj = self.env['hr.loan'].search(domain)
        for rec in loan_obj:
            if rec.employee_id not in employees_list:
                employees_list.append(rec.employee_id)
        for employee in employees_list:
            loan_values = []
            # total_paid = 0.0
            # total_unpaid = 0.0
            for loan in loan_obj:
                total_paid = 0.0
                total_unpaid = 0.0
                if employee.id == loan.employee_id.id:
                    for line in loan.loan_lines:
                        if line.paid:
                            total_paid += line.amount
                        else:
                            total_unpaid += line.amount 
                            # total_unpaid += line.amount
                    loan_values.append({'name': loan.name,
                                        'date_confirm': loan.date_confirm,
                                        'start_payment_date': loan.payment_date,
                                        'last_payment_date': loan.last_payment_date,
                                        'installment': loan.installment,
                                        'loan_amount': loan.loan_amount,
                                        'total_paid_amount': round(total_paid, 2),
                                        'balance_amount': round(total_unpaid, 2),
                                        })
            employee_data.append({'employee': employee.name,
                                  'employee_no': employee.employee_no,
                                  'loan_values': loan_values})

        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'data': employee_data,
            'date_from': date_from,
            'date_to': date_to,
        }
