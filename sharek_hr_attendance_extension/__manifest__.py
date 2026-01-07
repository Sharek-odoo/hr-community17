# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
{
    'name': "HR Attendance Extension (Saudi)",

    'summary': """hr attendance base customization""",

    'description': """
        hr attendance base customization
    """,

    'author': "",
    'category': 'Human Resources/Attendance',
    'version': '0.1',
    'author': "Sharek",
    'website': "https://sharek.com.sa",
    'depends': ['hr_contract','hr_attendance', 'sharek_hr_payroll_extension','sharek_hr_employee_extension'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        # 'data/payroll_data.xml',
        'data/salary_rules.xml',
        'data/hr_payroll_structure_data.xml',
        'views/hr_contract.xml',
        'views/hr_attendance.xml',
        'views/attendance_deduction_view.xml',
        'views/hr_sheet_print.xml',
        'views/hr_attendance_rules.xml'
    ],
    
}
