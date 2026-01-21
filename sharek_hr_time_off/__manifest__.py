# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
{
    "name": "Time off (Saudi)",
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
        'hr_holidays', 'sharek_hr_employee_extension','sharek_hr_timeoff_extension'
    ],
    "data": [
        'security/security.xml',
        'view/hr_leave.xml',
    ]
}
