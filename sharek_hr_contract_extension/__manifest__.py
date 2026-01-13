# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
{
    'name': "Contract Extension (Saudi)",

    'summary': """
       Contract Extension""",

    'description': """
        Contract Extension
    """,

    'author': "Sharek",
    'website': "https://sharek.com.sa",

    'category': 'Human Resource/Contract',
    'version': '17.0',

    # any module necessary for this one to work correctly
    'depends': ['base','hr','hr_contract', 'hr_holidays', 'om_hr_payroll','sharek_hr_employee_extension','analytic'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'data/hr_payroll_demo.xml',
        'views/hr_contract_view.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}
