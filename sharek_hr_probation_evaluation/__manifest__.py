# -*- coding: utf-8 -*-
{
    'name': "HR Probation Evaluation",

    'summary': "",

    'description': """

    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['hr','sharek_hr_contract_extension','sharek_contract_modification','sharek_employee_direct_work','hr_appraisal'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/probation_evaluation.xml',
        'views/hr_contract.xml',
    ],
    
}

