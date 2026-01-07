# -*- coding: utf-8 -*-
{
    'name': "HR Employee Penalty (Saudi)",

    'summary': """
        A module to manage hr employee penalties""",

    'description': """
        Long description of module's purpose
    """,
    'author': "My Company",
    'website': "http://www.yourcompany.com",
    'category': 'Human Resources',
    'version': '17.0',

    # any module necessary for this one to work correctly
    'depends': ['hr','sharek_hr_payroll_extension','sharek_hr_employee_extension','mail'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'data/penalty_data.xml',
    ],
}
