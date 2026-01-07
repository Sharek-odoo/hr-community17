# -- coding: utf-8 --
######################################################################################
#
#
#    Copyright (C) 2024 Sharek Telecom & IT Redefined(https://sharek.com.sa).
#    Author: Sharek Telecom & IT Redefined

{
    'name': 'Odoo17 Employee Contracts Types',
    'version': '17.0.0.1.0',
    'category': 'Generic Modules/Human Resources',
    'summary': """
        Contract type in contracts
    """,
    'description': """Odoo16 Employee Contracts Types,Odoo16 Employee, Employee Contracts, Odoo 16""",
    'author': 'Sharek',
    'company': 'Sharek',
    'website': 'https://sharek.com.sa',
    'depends': ['hr','hr_contract'],
    'data': [
        'security/ir.model.access.csv',
        'views/contract_view.xml',
        'data/hr_contract_type_data.xml',
    ],
    'installable': True,
    'images': ['static/description/banner.png'],
    'auto_install': False,
    'application': False,
    'license': 'AGPL-3',
}