# -*- coding: utf-8 -*-
{
    'name': "Employee Direct Work",
    'summary': "Custom Employee Direct Work",
    'description': """ Custom Employee Direct Work """,
    'author': "Hamid A Mohamed",
    'website': "https://www.yourcompany.com",
    'category': 'HR',
    'version': '0.1',
    'depends': ['base','mail','hr','sharek_hr_employee_extension'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/mail_template.xml',
        'views/employee_direct_work.xml',
        'views/hr_employee_views.xml',

    ],
}

