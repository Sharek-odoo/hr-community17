# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
{
    'name': "HR Government Relation",

    'summary': """
        A module to manage governments procedure""",

    'description': """
        Long description of module's purpose
    """,
    'author': "Sharek",
    'website': "https://sharek.com.sa",
    'category': 'Human Resources',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['hr_contract', 'sharek_hr_employee_extension', 'hr_holidays', 'account', 'mail', 'sharek_hr_employee_family',
                'om_hr_payroll'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings.xml',
        'views/exit_return.xml',
        'views/iqama_renewal.xml',
        'views/visit_renual.xml',
        'views/visit_type.xml',
    ],
}
