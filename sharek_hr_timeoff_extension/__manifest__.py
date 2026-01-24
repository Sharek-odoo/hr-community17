# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
{
    "name": "Time off extension (Saudi)",
    "summary": "Auto timeoff Allocation plus some attributes on leave type",
    "version": "0.1",
    'category': 'Human Resources/Leaves',
    'author': "Sharek",
    'website': "https://sharek.com.sa",
    "description": """
    * Add Calculation Type [Working Days, Calendar Days] in Leave Types
    * Auto sequencing of every timeoff request
    * Auto allocation
    Define both Annual leave type and days on employee contract
    """,
    'images': [
        'static/description/cover.png'
    ],

    "license": "OPL-1",
    "installable": True,
    "depends": [
        'hr_holidays', 'sharek_hr_employee_extension', 'hr_contract','sharek_hr_payroll_extension',
    ],
    "data": [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'data/ir_cron.xml',
        'data/hr_holidays_data.xml',
        'data/leave_plan.xml',
        'view/hr_leave_type.xml',
        'view/hr_leave.xml',
        'view/hr_leave_balance.xml',
        'view/hr_contract_view.xml',
        'view/hr_employee.xml',
        'view/timeoff_transfer_views.xml',
        'view/timeoff_not_transfer_views.xml',
    ]
}
