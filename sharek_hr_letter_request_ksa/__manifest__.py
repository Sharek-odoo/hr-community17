# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
{
    'name': "HR Letter Request",
    'summary': """Letter request management module""",
    'description': """
    """,
    'author': 'Sharek',
    'category': 'Human Resources',
    'version': '0.1',
    'website': "https://sharek.com.sa",
    'depends': ['sharek_hr_employee_extension','sharek_hr_payroll_extension'],
    'data': [
        'security/ir.model.access.csv',

        'data/sequence.xml',
        'data/salary_introduction_report_template.xml',
        'data/salary_transfer_report_template.xml',
        'data/letter_of_authority_report_template.xml',
        'data/experience_certificate_report_template.xml',

        'report/salary_introduction_template.xml',
        'report/salary_transfer_template.xml',
        'report/letter_of_authority_template.xml',
        'report/experience_certificate_template.xml',
        'report/report_action.xml',

        'views/service_request_view.xml',
        'views/res_config_settings.xml',

    ],
    'demo': [
    ],
}
