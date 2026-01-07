# -*- coding: utf-8 -*-

{
    'name': 'Hr Overtime (Saudi)',
    'version': '15.0',
    'summary': 'Manage Employee Overtime',
    'description': """
        Helps you to manage Employee Overtime.
        """,
    'category': 'Generic Modules/Human Resources',
    'author': "",
    # 'depends': [
    #     'sharek_hr_employee_extension', 'hr_contract', 'hr_attendance', 'hr_holidays', 'sharek_hr_payroll_extension'
    # ],
    'depends': [
        'hr_contract','om_hr_payroll', 'hr_attendance'
    ],
   
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/overtime_request_view.xml',
        'views/overtime_type.xml',
        'views/ir_config_settings.xml',
        'views/hr_contract.xml',
        # 'views/hr_payslip.xml',
        
        
    ],
    'demo': ['data/hr_overtime_demo.xml'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
