# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
{
    "name": "HR Employee Training (Saudi)",
    "summary": "",
    "version": "0.1",
    'category': 'Human Resources/Employee',
    'author': "Sharek",
    'website': "https://sharek.com.sa",
    "description": """
    """,

    "license": "OPL-1",
    "installable": True,
    "depends": [
        'sharek_hr_appraisal','base'
    ],
    "data": [
        'security/training_security.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'wizards/refused_reason.xml',
        'view/training_needs_form.xml',
        'view/training_menu_views.xml',
        'view/hr_employee_training.xml',
        'view/training_academy.xml',
    ],
}
