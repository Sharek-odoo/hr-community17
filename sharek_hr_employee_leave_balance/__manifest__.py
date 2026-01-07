# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined

{
    'name': 'HR Employee Leave Summary',
    'version': '1.0',
    'summary': 'Employee Salary and Leave Summary',
    'description': 'Track employee leave balances monthly.',
    'author': 'YourCompany',
    'author': "Sharek",
    'website': "https://sharek.com.sa",
    'category': 'Human Resources',
    'depends': ['base', 'hr','sharek_hr_employee_extension','sharek_hr_payroll_extension'],
    'data': [
        'security/security.xml',
        'data/data.xml',
        'views/hr_employee_summary_views.xml',
        'views/hr_employee_end_service_summary.xml',

        'report/employee_leave_report.xml',
    ],
    'application': True,
    'installable': True,
}

