# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined

{
    'name': "HR Payroll Analytic account",
    'summary': """Create entry from HR with analytic account in specific types of account""",
    'description': """
    """,
    'author': 'Sharek',
    'website': "https://sharek.com.sa",
    'category': 'Human Resources',
    'version': '0.1',
    'depends': ['om_hr_payroll'],
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        # 'security/security.xml',
        'views/res_config_settings_view.xml',
    ],
}
