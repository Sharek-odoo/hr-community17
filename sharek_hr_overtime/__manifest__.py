# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined

{
    'name': 'Hr Overtime (Saudi)',
    'version': '17.0',
    'website': "https://sharek.com.sa",
    'summary': 'Manage Employee Overtime',
    'description': """
        Helps you to manage Employee Overtime.
        """,
    'category': 'Generic Modules/Human Resources',
    'author': "Sharek",
    'depends': [
        'sharek_hr_employee_extension', 'hr_contract', 'hr_attendance', 'hr_holidays', 'sharek_hr_payroll_extension'
    ],
   
    'data': [

        'data/data.xml',
        'views/overtime_request_view.xml',
        'views/overtime_type.xml',
        'views/ir_config_settings.xml',
        'views/hr_contract.xml',
        # 'views/hr_payslip.xml',
        'security/ir.model.access.csv',
    ],
    'demo': ['data/hr_overtime_demo.xml'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
