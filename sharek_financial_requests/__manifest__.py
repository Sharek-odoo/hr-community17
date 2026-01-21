# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
{
    'name': "Sharek Financial Requests",

    'summary': """Customize hr""",

    'description': """
        Customize hr
    """,

    'author': "Sharek",
    'category': 'hr',
    'version': '17.0',
    'website': "https://sharek.com.sa",
    'depends': ['hr','account','sharek_hr_overtime','sharek_hr_employee_loan','sharek_hr_employee_family', 'sharek_hr_overtime'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/sequence_data.xml',
        'wizard/reject_reason.xml',
        'views/children_education_allowance_view.xml',
        'views/res_config_settings_view.xml',
        'views/advance_salary_view.xml',
        'views/financial_claim_view.xml',
        'views/overtime_request_view.xml',
        'views/perpetual_custody_view.xml',
        'views/temporary_custody_view.xml',
        'views/academic_year.xml',
        
    ],
    
}
