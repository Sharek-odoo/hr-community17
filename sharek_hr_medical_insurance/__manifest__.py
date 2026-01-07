# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
{
    'name': "HR Medical Insurance(Saudi)",

    'summary': """
        A module to manage hr medical insurance""",

    'description': """
        Long description of module's purpose
    """,
    'author': "Sharek",
    'website': "https://sharek.com.sa",
    'category': 'Human Resources',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['hr','sharek_hr_employee_family','sharek_hr_employee_loan','mail'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/policy_views.xml',
        'views/membership_views.xml',
        'views/res_config_settings.xml',
        'data/mail_data.xml',
    ],
}
