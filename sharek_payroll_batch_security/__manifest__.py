# -*- coding: utf-8 -*-
{
    'name': "sharek payroll batch security",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "sharek",
    'website': "http://www.sharek.com.sa",


    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base','sharek_hr_payroll_extension'],

    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
    
}
