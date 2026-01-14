# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
{
    'name': "Payroll Extension (Saudi)",

    'summary': """Customize payroll KSA bas""",

    'description': """
        Customize payroll KSA bas
    """,

    'author': "Sharek",
    'category': 'Human Resources/Payroll',
    'version': '15.0',
    'website': "https://sharek.com.sa",
    'depends': ['om_hr_payroll', 'hr_contract','om_hr_payroll_account','hr_grade_rank','sharek_hr_employee_extension','sharek_hr_payroll_analytic_account'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'wizard/payslip_payment.xml',
        'views/hr_contract_views.xml',
        'views/hr_payslip.xml',
        'views/hr_payslip_batch.xml',
        'data/hr_payroll_structure_data.xml',
        'data/hr_salary_rule_data.xml',
        'data/hr_payroll_structure_type_data.xml',
        # 'report/hr_payroll_report.xml',
    ],
    
}
