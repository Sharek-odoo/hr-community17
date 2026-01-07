# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined
{
    'name': "HR Sel Service Timeoff & Leaves",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Sharek",
    'website': "https://sharek.com.sa",


    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','website','sharek_hr_self_service_base','hr_holidays',],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # 'assets': {
    #     'web.assets_frontend': [
    #         'hr_self_service_contract/static/src/js/hr_selfservice.js',
    #     ],
    # },
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
