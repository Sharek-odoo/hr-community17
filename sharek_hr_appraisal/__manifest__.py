# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
{
    'name': 'Employee Appraisal Customization',
    'version': '17.0.0.1',
    'summary': 'Manage Employee Appraisal',
    'description': """
        Manage Employee Appraisal.
        """,
    'category': 'Generic Modules/Human Resources',
    'author': "Sharek",
    'website': "https://sharek.com.sa",
    'depends': ['sharek_hr_employee_extension', 'account'],
    'data': [
        'security/ir.model.access.csv',
        # 'security/security.xml',
        'data/ir_sequence.xml',
        'views/hr_appraisal_views.xml',
        'views/hr_appraisal_competence_views.xml',
        'views/hr_appraisal_level_views.xml',
        'views/hr_appraisal_goal_views.xml',
        'views/hr_employee_views.xml',
        'views/hr_appraisal_criteria_assignment_views.xml',
        'views/hr_appraisal_employee_views.xml'
        
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
}
