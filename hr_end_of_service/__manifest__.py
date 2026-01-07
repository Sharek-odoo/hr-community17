# -*- coding: utf-8 -*-
{
    'name': 'End of Service (Saudi)',
    'version': "15.0",
    "author": "",
    "license": "OPL-1",

    'sequence': 10,
    'category': 'Human Resources',

    'summary': 'End of Service, EOS, Employee End of Service, Benefits, EOS Contribution, Contribution, Reward, EOS Reward, Disengagement, Resignation',
    'description': """ Employee End of Service
""",
    'depends': [
        'sharek_hr_contract_extension',
        'sharek_hr_payroll_extension',
    ],
    'data': [
        'security/res_groups.xml',
        'security/ir_rule.xml',
        'security/ir.model.access.csv',
        'view/hr_end_of_service_reason.xml',
        'view/hr_end_of_service_termination_reason.xml',
        'view/hr_end_of_service.xml',
        'view/hr_payslip.xml',
        'view/action.xml',
        'view/menu.xml',
        'data/hr_end_of_service_reason.xml',
        'data/hr_end_of_service_termination_reason.xml',
        'data/hr_salary_rule.xml',
        'data/ir_config_parameter.xml',
        'data/ir_sequence.xml'
    ],
    'images': [

    ],

    'installable': True,
    'application': True,
    'odoo-apps': True
}
