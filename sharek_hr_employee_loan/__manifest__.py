# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
{
    'name': 'Employee Loan Management (Saudi)',
    'version': '16.0',
    'summary': 'Manage Loan Requests',
    'description': """
        Helps you to manage Loan Requests of your company's staff.
        """,
    'category': 'Generic Modules/Human Resources',
    'author': "Sharek",
    'website': "https://sharek.com.sa",
    # 'depends': [
    #     'base', 'hr','om_hr_payroll', 'account',
    # ],
    'depends': [
        'base', 'hr', 'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'wizards/reschedule_installment.xml',
        'wizards/loan_payment_register_views.xml',
        'wizards/employee_loan_report_wizard_views.xml',
        'reports/action_report.xml',
        'reports/loan_report_template.xml',
        'views/hr_loan.xml',
        'views/hr_loan_seq.xml',
        'data/salary_rule_loan.xml',
        'views/hr_loan_acc.xml',
        'views/hr_payroll.xml',
        'views/loan_type_views.xml',
        'views/hr_loan_config.xml',
        'views/hr_loan_installment_reschedule_view.xml'
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
