# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
{
    'name': "Sharek hr required fields",

    'summary': """
        make some fields  required """,

    'description': """
         make some fields  required
    """,

    'author': "Sharek",
    'website': "https://sharek.com.sa",

    'category': 'hr',
    'version': '17.0',

    # any module necessary for this one to work correctly
    'depends': ['base','hr','sharek_hr_employee_extension'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    
}
